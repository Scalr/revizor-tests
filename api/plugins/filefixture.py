# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import pytest
import requests

from pathlib import Path

from flex.core import load, validate_api_call, validate
from flex.exceptions import ValidationError

from api.utils.exceptions import FileNotFoundError
from api.utils.helpers import Defaults

class FileFixture(object):

    schemas_base_dir = "specifications"

    def __init__(self, request):
        self._request = request
        path = request.config.rootdir
        self.root_dir = Path(path.strpath)

    def load_validation_schema(self, pattern):
        search_criteria = dict(
            mask="{}.yaml".format(pattern),
            path="{}/swagger".format(self.schemas_base_dir))
        validation_schema = self._find(**search_criteria)
        return load(validation_schema.as_posix())

    def get_validation_schema(self, pattern):
        search_criteria = dict(
            mask="{}.yaml".format(pattern),
            path="{}/swagger".format(self.schemas_base_dir))
        return self._find(**search_criteria).as_posix()

    def _find(self, path, mask):
        path = self.root_dir.joinpath(path)
        result = list(path.rglob(mask))
        if not result:
            raise FileNotFoundError('Schema by mask {} not recursively found in {}'.format(
                mask,
                path.as_posix()
            ))
        return result[0]


class ValidationUtil(FileFixture):

    swagger_schema = None

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

    def __call__(self, schema, response, *args, **kwargs):
        result = list()
        for attr in self.__dir__():
            if attr.startswith("validate"):
                validation_error = getattr(self, attr)(schema, response)
                if validation_error:
                    result.append(validation_error)
        return result

    def _load(self, api_level):
        self.swagger_schema = self.load_validation_schema(api_level)

    def _get_raw_schema(self, api_level):
        if not self.swagger_schema:
            self._load(api_level)
        return self.swagger_schema

    def validate_api(self, api_level, response):
        """
        :type  api_level: str
        :param api_level:  schema name

        :type: response: requests.Response
        :param response: raw requests.response

        :return: None or validation error
        """
        try:
            validation_res = validate_api_call(
                self._get_raw_schema(api_level),
                raw_request=response.request,
                raw_response=response)
        except (ValidationError, ValueError) as e:
            validation_res = e
        return validation_res

    def validate_json(self, api_level, data):
        """
        :type  api_level: str
        :param api_level:  schema name

        :type: data: requests.Response or dict
        :param data: raw requests.response or dict

        :return: None or validation error
        """
        if isinstance(data, requests.models.Response):
            data = data.json()
        try:
            validation_res = validate(
                self._get_raw_schema(api_level),
                data
            )
        except (ValidationError, ValueError) as e:
            validation_res = e
        return validation_res

    def validate_request(self, schema, req_params):
        method = req_params.get('method')
        params = req_params.get('params')

        # Validate request type
        available_methods = {rt: m for rt, m in Defaults.request_types.items() if m in schema.keys()}
        http_meth = available_methods.get(method)
        if not http_meth:
            raise ValueError("Not supported endpoint request type, got {0}, expected {1}".format(
                method,
                available_methods.keys()))

        # Validate request required params
        if not isinstance(params, dict):
            raise TypeError('Request params mismatch')
        required_params = [p.name for p in schema[http_meth].parameters if p.required]
        if not list(params.keys()).sort() == required_params.sort():
            raise ValueError("Not enough required parameters got {0}, expected {1}".format(
                params,
                required_params))
        return dict(
            method=http_meth,
            endpoint=req_params.get('endpoint'),
            params=params,
            body=req_params.get('body'),
            filters=req_params.get('filters'))


@pytest.fixture(scope="session")
def fileutil(request):
    return FileFixture(request)
