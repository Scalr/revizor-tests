class CognitoIdentity(object):
    service_name = 'cognito identity'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('cognito-identity')
