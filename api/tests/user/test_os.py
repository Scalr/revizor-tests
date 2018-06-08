# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest


swagger_schemas = ("user",)


class TestUserApiOs(object):

    def test_os_list(self, request, fileutil, api_session, validationutil):
        schema = fileutil.get_request_schema(request.node.name)

    def test_os_get(self, api_session):
        pass
