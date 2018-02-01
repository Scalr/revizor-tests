class DynamoDb(object):
    service_name = 'dynamodb'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('dynamodb')
