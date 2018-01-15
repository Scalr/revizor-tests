import boto3
from botocore import config as boto_config

from integration.terrain.libs.cloud_services import CloudServiceBase


class Ec2CloudService(CloudServiceBase):
    """
    Base class for AWS services.
    Contains AWS-specific logic that is common for all services
    """
    region = 'us-east-1'

    def __init__(self, request_id, secret):
        super(Ec2CloudService, self).__init__(request_id, secret)
        self.client_config = None
        self.session = None

    def configure(self):
        super(Ec2CloudService, self).configure()
        self.client_config = boto_config.Config(
            proxies={
                'https': self.csg_proxy
            })
        self.session = boto3.Session(aws_access_key_id=self.request['access_key'],
                                     aws_secret_access_key=self.secret,
                                     region_name=Ec2CloudService.region)

    def _verify_impl(self):
        raise NotImplementedError()
