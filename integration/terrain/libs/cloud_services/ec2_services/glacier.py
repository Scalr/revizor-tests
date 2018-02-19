class Glacier(object):
    service_name = 'glacier'
    log_records = ['CONNECT glacier.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('glacier')
        assert isinstance(client.list_vaults()['VaultList'], list)
