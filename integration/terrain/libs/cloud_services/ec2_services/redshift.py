from botocore import exceptions as boto_exceptions
from lettuce import world


class Redshift(object):
    service_name = 'redshift'
    log_records = ['https://redshift.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('redshift')
        assert isinstance(client.describe_clusters()['Clusters'], list)

    def verify_denied(self, error_text):
        client = self.platform.get_client('redshift')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.describe_clusters()
