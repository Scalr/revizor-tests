# coding: utf-8
"""
Created on 18.06.18
@author: Eugeny Kurkovich
"""
import json

import pytest

from api.plugins.filefixture import FileNotFoundError
from api.utils.session import ScalrApiSession
from api.utils.helpers import RequestSchemaFormatter


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

    def execute_request(self, schema, validate='api'):
        """
        :type schema: Box object
        :param schema: Python dictionaries with advanced dot notation access

        :type: valdate: str
        :param validate: api, json, both

        :return: Box object from requests.Response.json(), raw response
        """
        try:
            request_params = dict(
                method=schema.method,
                endpoint=schema.endpoint,
                body=schema.body,
                params=schema.params
            )
            response = self.session.request(**request_params)
            json_data = RequestSchemaFormatter(response.json())
        except json.JSONDecodeError:
            json_data = None
        validation_res = getattr(
            self.validationutil,
            validate,
            self.validationutil)(
            schema.swagger_schema,
            response)
        assert not validation_res
        return response, json_data

