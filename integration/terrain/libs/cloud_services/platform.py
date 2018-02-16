from datetime import datetime

import boto3
import os
import requests
from azure.common.credentials import ServicePrincipalCredentials
from botocore import config as boto_config
from lettuce import world

import azure_services
import ec2_services
from revizor2.backend import IMPL
from revizor2.conf import CONF
from revizor2.utils import env_vars


class CloudServicePlatform(object):
    """Base class for cloud services. Contains platform-independent logic"""
    services = {}

    def __init__(self, request_id, secret):
        self.request_id = request_id
        self.secret = secret
        self.cacert_path = os.path.join(CONF.main.keysdir, 'csg-%s.pem' % self.request_id)
        self.csg_proxy = None
        self.request = None

    def configure(self):
        """Download PEM certificate if needed and prepare session for service requests"""
        self.request = IMPL.csg.get_request(self.request_id)

        te_url = '%s.test-env.scalr.com' % CONF.scalr.te_id
        csg_port = world.get_scalr_config_value('scalr.csg.endpoint.port')
        self.csg_proxy = '%s:%s' % (te_url, csg_port)

        if not os.path.exists(CONF.main.keysdir):
            os.makedirs(CONF.main.keysdir)
        if not os.path.exists(self.cacert_path):
            r = requests.get('http://csg/cert/pem', proxies={'http': self.csg_proxy})
            with open(self.cacert_path, 'w') as f:
                f.write(r.text)

    @classmethod
    def get_service(cls, service_name):
        if service_name not in cls.services:
            raise NotImplementedError('Service %s is not supported in %s' % (service_name, cls.__name__))
        return cls.services[service_name]

    def verify(self, service_name):
        service = self.get_service(service_name)(self)
        self._verify_impl(service)

    def _verify_impl(self, service):
        raise NotImplementedError()

    @staticmethod
    def get_test_name(*args):
        if not args:
            args = ['']
        suffix = datetime.now().strftime('%m%d%H%M%S')
        names = ['revizortest%s%s' % (name, suffix) for name in args]
        return names[0] if len(args) == 1 else names


class Ec2ServicePlatform(CloudServicePlatform):
    """
    Base class for AWS services.
    Contains AWS-specific logic that is common for all services
    """
    services = ec2_services.services
    region = 'us-east-1'

    def __init__(self, request_id, secret):
        super(Ec2ServicePlatform, self).__init__(request_id, secret)
        self.client_config = None
        self.session = None

    def configure(self):
        super(Ec2ServicePlatform, self).configure()
        self.client_config = boto_config.Config(
            proxies={
                'https': self.csg_proxy
            })
        self.session = boto3.Session(aws_access_key_id=self.request['access_key'],
                                     aws_secret_access_key=self.secret,
                                     region_name=Ec2ServicePlatform.region)

    def get_client(self, service_name, region=None):
        return self.session.client(service_name,
                                   verify=self.cacert_path,
                                   config=self.client_config,
                                   region_name=region or Ec2ServicePlatform.region)

    def _verify_impl(self, service):
        service.verify()


class AzureServicePlatform(CloudServicePlatform):
    """
    Base class for Azure services.
    Contains Azure-specific logic that is common for all services
    """
    services = azure_services.services

    def __init__(self, request_id, secret):
        super(AzureServicePlatform, self).__init__(request_id, secret)
        self.credentials = None
        self.subscription_id = None
        self.resource_group_name = 'revizor'

    def configure(self):
        super(AzureServicePlatform, self).configure()
        # some azure management clients strictly require subscription_id parameter
        # to be of type `str`, and fail when it's `unicode`
        self.subscription_id = str(self.request['cc_id'])
        with env_vars(https_proxy='http://%s' % self.csg_proxy,
                      REQUESTS_CA_BUNDLE=self.cacert_path):
            self.credentials = ServicePrincipalCredentials(
                client_id=self.request['client_id'],
                secret=self.secret,
                tenant=self.request['tenant_id']
            )

    def _verify_impl(self, service):
        with env_vars(https_proxy='http://%s' % self.csg_proxy,
                      REQUESTS_CA_BUNDLE=self.cacert_path):
            service.verify()
