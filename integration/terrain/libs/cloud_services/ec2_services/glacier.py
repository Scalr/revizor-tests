from botocore import exceptions as boto_exceptions
from lettuce import world


class Glacier(object):
    service_name = 'glacier'
    log_records = ['https://glacier.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('glacier')
        assert isinstance(client.list_vaults()['VaultList'], list)

    def verify_denied(self, error_text):
        client = self.platform.get_client('glacier')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_vaults()
