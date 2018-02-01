class StreamAnalytics(object):
    service_name = 'stream analytics'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        pass
