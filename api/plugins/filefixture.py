# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import json

import pytest
import requests


from pathlib import Path
from flex.core import load, validate_api_call, validate
from flex.exceptions import ValidationError


class FileNotFoundError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class FileFixture(object):

    schemas_base_dir = "specifications"

    def __init__(self, request, *args, **kwargs):
        self._request = request
        path = request.config.rootdir
        self.root_dir = Path(path.strpath)

    def get_request_schema(self, pattern):
        delimiter = "_"
        path_suffix = "test"
        if pattern.startswith(path_suffix):
            pattern = delimiter.join(pattern.split(delimiter)[1:])
        search_criteria = dict(
            mask="*{}*.json".format(pattern),
            path="{}/{}".format(self.schemas_base_dir, path_suffix))
        with self._find(**search_criteria).open() as schema:
            return json.load(schema)

    def get_validation_schema(self, pattern):
        path_suffix = "swagger"
        search_criteria = dict(
            mask="{}.yaml".format(pattern),
            path="{}/{}".format(self.schemas_base_dir, path_suffix))
        validation_schema = self._find(**search_criteria)
        return load(validation_schema.as_posix())

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

    swagger_schemas = {
        "user": None,
        "account": None,
        "global": None
    }

    def __init__(self, request, schemas, *args, **kwargs):
        shemas = schemas or list(self.swagger_schemas.keys())
        super().__init__(request, *args, **kwargs)
        self._load(shemas)

    def _load(self, schemas):
        for schema in schemas:
            self.swagger_schemas.update({schema: self.get_validation_schema(schema)})

    def validate_api(self, schema, response):
        """
        :type  schema: str
        :param schema:  schema name

        :type: response: requests.Response
        :param response: raw requests.response

        :return: None or validation error
        """
        try:
            validation_res = validate_api_call(
                self.swagger_schemas[schema],
                raw_request=response.request,
                raw_response=response)
        except (ValidationError, ValueError) as e:
            validation_res = e
        return validation_res

    def validate_json(self, schema, data):
        """
        :type  schema: str
        :param schema:  schema name

        :type: data: requests.Response or dict
        :param data: raw requests.response or dict

        :return: None or validation error
        """
        if isinstance(data, requests.models.Response):
            data = data.json()
        try:
            validation_res = validate(
                self.swagger_schemas[schema],
                data
            )
        except (ValidationError, ValueError) as e:
            validation_res = e
        return validation_res


@pytest.fixture(scope="session")
def fileutil(request):
    return FileFixture(request)


@pytest.fixture(scope="module", autouse=True)
def validationutil(request):
    schemas = getattr(request.module, "swagger_schemas", None)
    return ValidationUtil(request, schemas)

