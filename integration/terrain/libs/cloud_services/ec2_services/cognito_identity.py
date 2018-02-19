from botocore import exceptions as boto_exceptions
from lettuce import world


class CognitoIdentity(object):
    service_name = 'cognito identity'
    log_records = ['CONNECT cognito-identity.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('cognito-identity')
        pool_name = self.platform.get_test_name()
        pool_id = client.create_identity_pool(IdentityPoolName=pool_name,
                                              AllowUnauthenticatedIdentities=True)['IdentityPoolId']
        assert any([pool for pool in client.list_identity_pools(MaxResults=10)['IdentityPools']
                    if pool['IdentityPoolName'] == pool_name])
        assert client.describe_identity_pool(IdentityPoolId=pool_id)['IdentityPoolName'] == pool_name
        pool_name = pool_name + 'a'
        client.update_identity_pool(IdentityPoolId=pool_id,
                                    IdentityPoolName=pool_name,
                                    AllowUnauthenticatedIdentities=False)
        pool = client.describe_identity_pool(IdentityPoolId=pool_id)
        assert pool['IdentityPoolName'] == pool_name
        assert not pool['AllowUnauthenticatedIdentities']
        assert len(client.list_identities(IdentityPoolId=pool_id, MaxResults=10)['Identities']) == 0
        client.delete_identity_pool(IdentityPoolId=pool_id)
        with world.assert_raises(boto_exceptions.ClientError, 'ResourceNotFoundException'):
            client.describe_identity_pool(IdentityPoolId=pool_id)
