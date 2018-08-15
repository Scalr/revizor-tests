# coding: utf-8
"""
Created on 12.07.18
@author: Eugeny Kurkovich
"""

import requests

from api.utils.helpers import remove_empty_values
from api.utils.consts import APIParams
from api.utils.exceptions import ResponseValidationError

from flex.core import load as load_schema_from_file, validate as validate_response
from flex.exceptions import ValidationError


class ValidationUtil(object):

    _swagger_schema = None

    _successful_response_codes = dict(
        GET=200,
        PATCH=200,
        POST=201,
        DELETE=204
    )

    def __init__(self, api_level, fileutil):
        self._fileutil = fileutil
        self._api_level = api_level

    def _load(self):
        path = self._fileutil.get_swagger_difinitions(self._api_level)
        self._swagger_schema = load_schema_from_file(path)

    def _get_raw_schema(self):
        if not self._swagger_schema:
            self._load()
        return self._swagger_schema

    def request_ok(self, response):
        response_successful_code = self._successful_response_codes.get(response.request.method)
        if not response.status_code == response_successful_code:
            raise ResponseValidationError('Response successful code not valid')

    def validate(self, data, flex_validation=False):
        """
        :type: data: requests.Response
        :param data: raw requests.response

        :type: flex_validation: bool
        :param: flex_validation: Enabled response validation by flex

        :return: None or validation error
        """
        if not isinstance(data, requests.models.Response):
            raise ValueError('Not valid data format')
        self.request_ok(data)
        if flex_validation:
            try:
                data = data.json()
                validation_res = validate_response(
                    self._get_raw_schema(),
                    data
                )
            except (ValidationError, ValueError) as e:
                validation_res = e
        else:
            validation_res = None
        return validation_res

    @staticmethod
    def check_request_params(schema, req_params):
        method = req_params.get('method')
        params = req_params.get('params')
        filters = remove_empty_values(req_params.get('filters'))
        body = remove_empty_values(req_params.get('body'))

        # Validate request type
        available_methods = {rt: m for rt, m in APIParams.request_types.items() if m in schema.keys()}
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
            body=body,
            filters=filters)


