class Route53(object):
    service_name = 'route53'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('route53')
