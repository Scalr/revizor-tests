class Lambda(object):
    service_name = 'lambda'
    log_records = ['https://lambda.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('lambda')
        assert isinstance(client.list_functions()['Functions'], list)
