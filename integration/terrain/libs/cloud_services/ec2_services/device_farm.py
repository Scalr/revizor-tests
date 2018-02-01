class DeviceFarm(object):
    service_name = 'device farm'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('devicefarm')
