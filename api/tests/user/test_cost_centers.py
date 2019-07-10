import pytest
import requests


class TestCostCentersUserScope(object):
    env_id = "5"
    cost_center_id = "3f54770e-bf1a-11e3-92c5-000feae9c516"
    invalid_envId = "1"

        #env_cc_list
    def test_cost_centers_env_list(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/cost-centers/",
            params=dict(
                envId=self.env_id))
        assert resp.json()['data'][0]['id'] == self.cost_center_id

    def test_cost_centers_invalid_environment_list(self, api):
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
                "/api/v1beta0/user/envId/cost-centers/",
                params=dict(
                envId=self.invalid_envId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

        #env_cc_get
    def test_cost_centers_get(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/cost-centers/costCenterId/",
            params=dict(
                envId=self.env_id,
                costCenterId=self.cost_center_id))
        assert resp.json()['data']['id'] == self.cost_center_id    

class TestCostCentersAccountScope(object):
    account_id = "1"
    invalid_account_id = "10"
    cost_center_Id = "3f54770e-bf1a-11e3-92c5-000feae9c516"

        #acc_cc_list
    def test_cost_centers_acc_list(self, api):
        resp = api.list(
            "/api/v1beta0/account/accountId/cost-centers/",
            params=dict(
                accountId=self.account_id))
        assert resp.json()['data'][0]['id']

    def test_cost_centers_invalid_acc_list(self, api):
        invalid_account_id = "90"
        with pytest.raises(requests.exceptions.HTTPError) as error:
            resp = api.list(
            "/api/v1beta0/account/accountId/cost-centers/",
            params=dict(
                accountId=self.invalid_account_id))
        assert error.value.response.status_code == 404

        #acc_cc_get
    def test_cost_centers_acc_get_params(self, api):
        resp = api.list(
            "/api/v1beta0/account/accountId/cost-centers/costCenterId/",
            params=dict(
                accountId=self.account_id,
                costCenterId=self.cost_center_Id))
        assert resp.json()['data']['id']
        assert resp.json()['data']['name']
        assert resp.json()['data']['billingCode']
