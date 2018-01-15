import os
import requests

from revizor2.backend import IMPL
from revizor2.conf import CONF
from revizor2.testenv import TestEnv
from revizor2.utils import get_dict_value


class CloudServiceBaseMeta(type):
    """
    Metaclass is used to provide some common class attributes
    to cloud service classes, which cannot be inherited directly
    due to their mutable type
    """
    def __init__(cls, *args):
        super(CloudServiceBaseMeta, cls).__init__(*args)
        cls.services = {}


class CloudServiceBase(object):
    """Base class for cloud services. Contains platform-independent logic"""
    __metaclass__ = CloudServiceBaseMeta
    log_records = []

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
        te_cfg = TestEnv(CONF.scalr.te_id).get_config()
        csg_port = get_dict_value(te_cfg, 'scalr.csg.endpoint.port')
        self.csg_proxy = '%s:%s' % (te_url, csg_port)

        if not os.path.exists(CONF.main.keysdir):
            os.makedirs(CONF.main.keysdir)
        if not os.path.exists(self.cacert_path):
            r = requests.get('http://csg/cert/pem', proxies={'http': self.csg_proxy})
            with open(self.cacert_path, 'w') as f:
                f.write(r.text)

    @classmethod
    def get_service(cls, platform, name):
        """Service factory method"""
        from ec2.base_ec2 import Ec2CloudService
        from azure.base_azure import AzureCloudService
        if platform == 'ec2':
            cloud_base = Ec2CloudService
        elif platform == 'azure':
            cloud_base = AzureCloudService
        else:
            raise NotImplementedError('Platform %s is not supported' % platform)
        if name not in cloud_base.services:
            raise NotImplementedError('Service %s is not supported in %s' % (name, cloud_base.__name__))
        return cloud_base.services[name]

    @classmethod
    def register(cls, service_name):
        """
        Decorator is used to register services in it's base (platform) class.
        This makes implementing new services simpler and prevents modifying modules
        other than service module itself
        """
        def decorator(service_class):
            cls.services[service_name] = service_class
            return service_class

        return decorator

    def verify(self):
        self._verify_impl()

    def _verify_impl(self):
        """Actual service calls test. Must be implemented in every particular service class"""
        raise NotImplementedError()
