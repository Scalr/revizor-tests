# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest


class TestOs(object):

    env_id = "5"
    os_id = "ubuntu-14-04"

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def test_os_list(self):
        # Execute request
        resp = self.api.list(
            "/api/v1beta0/user/envId/os/",
            params=dict(envId=self.env_id),
            filters=dict(id=self.os_id))
        assert resp.json_data.data[0].id == self.os_id

    def test_os_get(self):
        # Execute request
        resp = self.api.get(
            "/api/v1beta0/user/envId/os/osId/",
            params=dict(
                envId=self.env_id,
                osId=self.os_id))
        assert resp.json_data.data.id == self.os_id
