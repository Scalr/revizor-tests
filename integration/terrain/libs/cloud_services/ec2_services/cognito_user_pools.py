from botocore import exceptions as boto_exceptions
from lettuce import world


class CognitoUserPools(object):
    service_name = 'cognito user pools'
    log_records = ['CONNECT cognito-idp.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('cognito-idp')
        pool_name = self.platform.get_test_name()
        pool_id = client.create_user_pool(PoolName=pool_name)['UserPool']['Id']
        assert any([pool for pool in client.list_user_pools(MaxResults=10)['UserPools']
                    if pool['Name'] == pool_name])
        assert client.describe_user_pool(UserPoolId=pool_id)['UserPool']['Name'] == pool_name
        client.update_user_pool(UserPoolId=pool_id, EmailVerificationSubject='subj')
        assert client.describe_user_pool(UserPoolId=pool_id)['UserPool']['VerificationMessageTemplate']['EmailSubject'] == 'subj'
        client.delete_user_pool(UserPoolId=pool_id)
        with world.assert_raises(boto_exceptions.ClientError, 'ResourceNotFoundException'):
            client.describe_user_pool(UserPoolId=pool_id)