class Mobile(object):
    service_name = 'mobile'
    log_records = ['CONNECT mobile.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('mobile')
        assert isinstance(client.list_projects(maxResults=10)['projects'], list)
        assert len(client.list_bundles(maxResults=10)['bundleList']) > 0
        assert client.describe_bundle(bundleId='demo-app')['details']['title'] == 'Demo Mobile App Project'
