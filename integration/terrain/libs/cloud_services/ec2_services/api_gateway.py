from botocore import exceptions as boto_exceptions
from lettuce import world


class ApiGateway(object):
    service_name = 'api gateway'
    log_records = ['https://apigateway.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('apigateway')
        api_name = self.platform.get_test_name('api')
        api_id = client.create_rest_api(name=api_name,
                                        description='Api for Revizor Tests',
                                        endpointConfiguration={
                                            'types': ['EDGE', ]
                                        })['id']
        assert any([api for api in client.get_rest_apis()['items'] if api['name'] == api_name])
        assert client.get_rest_api(restApiId=api_id)['name'] == api_name
        client.delete_rest_api(restApiId=api_id)
        with world.assert_raises(boto_exceptions.ClientError, 'NotFound'):
            client.get_rest_api(restApiId=api_id)

    def verify_denied(self, error_text):
        client = self.platform.get_client('apigateway')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.get_rest_apis()
