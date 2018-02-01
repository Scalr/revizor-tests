class ApiGateway(object):
    service_name = 'api gateway'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('apigateway')
