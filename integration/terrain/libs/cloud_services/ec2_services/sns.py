class Sns(object):
    service_name = 'sns'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('sns')
