class Redshift(object):
    service_name = 'redshift'
    log_records = ['https://redshift.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('redshift')
        assert isinstance(client.describe_clusters()['Clusters'], list)
