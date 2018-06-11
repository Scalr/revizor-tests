# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest


swagger_schemas = ("user",)


class TestUserApiOs(object):

    @pytest.mark.parametrize('endpoint', ({"params": {"envId": 5}},))
    def test_os_list(self, request, fileutil, api_session, validationutil, endpoint):
        request_schema = fileutil.get_request_schema(request.node.originalname)
        request_schema['request']['endpoint'].update(endpoint)
        resp = api_session.request(**request_schema['request'])
        assert not validationutil.validate_api(request_schema['response']['swagger_schema'], resp)
        assert not validationutil.validate_json(request_schema['response']['swagger_schema'], resp)

    def test_os_get(self, api_session):
        pass
