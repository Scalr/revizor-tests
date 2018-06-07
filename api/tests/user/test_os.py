# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import pytest


class TestUserApiOs(object):

    def test_user_os_list(self, request, fileutil):
        spec = fileutil.get_spesification_by_test_name(request.node.name)
        print(spec)

    def test_user_os_get(self, api_session):
        pass
