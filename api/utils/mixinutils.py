# coding: utf-8
"""
Created on 18.06.18
@author: Eugeny Kurkovich
"""
import json

import pytest

from box import Box

from api.plugins.filefixture import FileNotFoundError
from api.plugins.session import ScalrApiSession


RELATIVE_CONF_PATH = 'conf/environment.json'


class SessionMixin(object):

    session = None
    validationutil = None

    @pytest.fixture(autouse=True)
    def create_session(self, request, fileutil, validationutil):
        credentials_path = fileutil.root_dir.joinpath(RELATIVE_CONF_PATH)
        if not credentials_path.exists():
            raise FileNotFoundError(
                "Credentials is unavailable, {} not found".format(
                    credentials_path.as_poasix()))
        with credentials_path.open() as f:
            credentials = json.load(f)
            self.session = ScalrApiSession(**credentials)
            self.validationutil = validationutil
        request.addfinalizer(self.session.close)

    def get(self, request_schema, validate=None):
        """
        :type request_schema: Box object
        :param request_schema: Python dictionaries with advanced dot notation access

        :type: valdate: str
        :param validate: api, json, both

        :return: Box object from requests.Response.json(), raw response
        """
        response = self.session.request(**request_schema.request.to_dict())
        if validate:
            validation_res = getattr(self.validationutil, validate, self.validationutil)(
                request_schema.response.swagger_schema,
                response
            )
            assert not validation_res
        return Box(response.json()), response

