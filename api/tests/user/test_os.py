# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest

from api.utils.mixinutils import SessionMixin


swagger_schemas = "user"


class TestUserApiOs(SessionMixin):

    env_id = "5"
    os_id = "ubuntu-14-04"

    def test_os_list(self, fileutil):
        os_family = "ubuntu"
        # Get request schema
        r_schema = fileutil.get_request_schema("os_list")
        # Set up request params
        r_schema.endpoint.params.envId = self.env_id
        r_schema.params = dict(family=os_family)
        # Execute request
        _, json_data = self.execute_request(r_schema)
        assert any(os.id == self.os_id for os in json_data.data)

    def test_os_get(self, fileutil):
        r_schema = fileutil.get_request_schema("os_get")
        # Set up request params
        r_schema.endpoint.params.envId = self.env_id
        r_schema.endpoint.params.osId = self.os_id
        # Execute request
        _, json_data = self.execute_request(r_schema)
        assert json_data.data.id == self.os_id
