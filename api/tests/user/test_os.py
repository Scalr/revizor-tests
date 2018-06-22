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

    def test_os_list(self, fileutil):
        os_family = "ubuntu"
        os_generation = "14.04"
        # Get request schema
        r_schema = fileutil.get_request_schema("os_list")
        # Set up request params
        r_schema.endpoint.params.envId = self.env_id
        r_schema.params = dict(
            family=os_family,
            generation=os_generation)
        # Execute request
        _, json_data = self.execute_request(r_schema)
        assert json_data.data[0].family == os_family
        assert json_data.data[0].generation == os_generation

    #def test_os_get(self, fileutil):
    #    request_schema = fileutil.get_request_schema("os_get")
    #    _, json_data = self.get(request_schema, validate='json')
    #    with pytest.raises(AssertionError):
    #        assert set(request_schema.response.data.items()).issubset(json_data.data.items())
