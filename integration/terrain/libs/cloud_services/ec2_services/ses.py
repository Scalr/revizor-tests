class Ses(object):
    service_name = 'ses'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('ses')
