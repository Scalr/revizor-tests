class Lambda(object):
    service_name = 'lambda'
    log_records = ['CONNECT lambda.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('lambda')
        assert isinstance(client.list_functions()['Functions'], list)
