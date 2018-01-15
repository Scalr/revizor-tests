from base_ec2 import Ec2CloudService

from botocore import exceptions as boto_exceptions


@Ec2CloudService.register('lambda')
class Lambda(Ec2CloudService):
    log_records = ['CONNECT lambda.us-east-1.amazonaws.com:443']

    def _verify_impl(self):
        client = self.session.client('lambda', verify=self.cacert_path, config=self.client_config)
        try:
            result = client.list_functions()
            assert result['Functions'] == []
        except boto_exceptions.ClientError as e:
            raise AssertionError(e.message)
