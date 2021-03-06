from botocore import exceptions as boto_exceptions
from lettuce import world


class Mobile(object):
    service_name = 'mobile'
    log_records = ['https://mobile.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('mobile')
        assert isinstance(client.list_projects(maxResults=10)['projects'], list)
        assert len(client.list_bundles(maxResults=10)['bundleList']) > 0
        assert client.describe_bundle(bundleId='demo-app')['details']['title'] == 'Demo Mobile App Project'

    def verify_denied(self, error_text):
        client = self.platform.get_client('mobile')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_projects(maxResults=10)
