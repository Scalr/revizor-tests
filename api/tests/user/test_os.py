# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest


swagger_schemas = ("user",)


class TestUserApiOs(object):

    os_id = None

    # Example: redefine endpoint params from request schema
    @pytest.mark.parametrize('endpoint', ({"params": {"envId": 5}},))
    def test_os_list(self, request, fileutil, api_session, validationutil, endpoint):
        node = request.node
        request_schema = fileutil.get_request_schema(node.originalname or node.name)
        request_schema['request']['endpoint'].update(endpoint)
        resp = api_session.request(**request_schema['request'])
        # Validate response with swagger schema
        assert not validationutil.validate_api(request_schema['response']['swagger_schema'], resp)
        assert not validationutil.validate_json(request_schema['response']['swagger_schema'], resp)
        # pass test result as argument to another test
        TestUserApiOs.os_id = resp.json().get('data', [{}])[0].get('id', None)

    def test_os_get(self, request, fileutil, api_session, validationutil):
        node = request.node
        request_schema = fileutil.get_request_schema(node.originalname or node.name)
        # redefine argument from request schema use first test result
        request_schema['request']['endpoint']['params']['osId'] = TestUserApiOs.os_id
        resp = api_session.request(**request_schema['request'])
        assert not validationutil.validate_json(request_schema['response']['swagger_schema'], resp)
        # example: validate response with request schema data
        json_data = resp.json().get('data', {})
        assert set(request_schema['response']['data'].items()).issubset(json_data.items())
