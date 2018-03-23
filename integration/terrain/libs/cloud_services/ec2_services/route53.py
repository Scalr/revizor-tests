from botocore import exceptions as boto_exceptions
from lettuce import world


class Route53(object):
    service_name = 'route53'
    log_records = ['https://route53.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('route53')
        ref_name = self.platform.get_test_name()
        dset_id = client.create_reusable_delegation_set(CallerReference=ref_name)['DelegationSet']['Id']
        assert any([dset for dset in client.list_reusable_delegation_sets()['DelegationSets']
                    if dset['CallerReference'] == ref_name])
        assert client.get_reusable_delegation_set(Id=dset_id)['DelegationSet']['CallerReference'] == ref_name
        client.delete_reusable_delegation_set(Id=dset_id)
        with world.assert_raises(boto_exceptions.ClientError, 'NoSuchDelegationSet'):
            client.get_reusable_delegation_set(Id=dset_id)

    def verify_denied(self, error_text):
        client = self.platform.get_client('route53')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_reusable_delegation_sets()
