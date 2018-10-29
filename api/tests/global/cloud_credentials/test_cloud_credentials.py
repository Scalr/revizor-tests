import pytest


app_level = 'global'


class TestCloudCredentials:
    scope = 'global'

    def test_list_cc(self, api):
        cc = api.list('/api/v1beta0/global/cloud-credentials/', params={})
        print(cc)

    def test_get_cc(self):
        pass

    def test_get_invalid_cc(self):
        pass

    def test_delete_cc(self):
        pass

    def test_delete_invalid_cc(self):
        pass

    def test_create_aws_cc(self):
        pass
