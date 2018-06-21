# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest

from api.utils.mixinutils import SessionMixin


swagger_schemas = "user"


class TestUserApiOs(SessionMixin):

    def test_os_list(self, fileutil):
        self.get(fileutil.get_request_schema("os_list"), validate='both')

    def test_os_get(self, fileutil):
        request_schema = fileutil.get_request_schema("os_get")
        _, json_data = self.get(request_schema, validate='json')
        with pytest.raises(AssertionError):
            assert set(request_schema.response.data.items()).issubset(json_data.data.items())
