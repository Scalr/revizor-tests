from botocore import exceptions as boto_exceptions
from lettuce import world


class Lambda(object):
    service_name = 'lambda'
    log_records = ['https://lambda.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('lambda')
        assert isinstance(client.list_functions()['Functions'], list)

    def verify_denied(self, error_text):
        client = self.platform.get_client('lambda')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_functions()
