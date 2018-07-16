# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest

app_level = "user"


class TestOs(object):

    env_id = "5"
    os_id = "ubuntu-14-04"

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def test_os_list(self):
        # Execute request
        resp, validation_result = self.api.list(
            "/api/v1beta0/user/envId/os/",
            params=dict(envId=self.env_id),
            filters=dict(id=self.os_id))
        assert resp.json()['data'][0]['id'] == self.os_id
        assert not validation_result, validation_result

    def test_os_get(self):
        # Execute request
        resp, validation_result = self.api.get(
            "/api/v1beta0/user/envId/os/osId/",
            params=dict(
                envId=self.env_id,
                osId=self.os_id))
        assert resp.json()['data']['id'] == self.os_id
        assert not validation_result, validation_result
