from botocore import exceptions as boto_exceptions


class Lambda(object):
    service_name = 'lambda'
    log_records = ['CONNECT lambda.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client(Lambda.service_name)
        try:
            result = client.list_functions()
            assert result['Functions'] == []
        except boto_exceptions.ClientError as e:
            raise AssertionError(e.message)
