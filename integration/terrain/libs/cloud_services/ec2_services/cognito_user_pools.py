class CognitoUserPools(object):
    service_name = 'cognito user pools'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('cognito-idp')
