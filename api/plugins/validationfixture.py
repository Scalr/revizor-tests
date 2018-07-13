# coding: utf-8
"""
Created on 12.07.18
@author: Eugeny Kurkovich
"""

import requests

from api.utils.helpers import Defaults

from flex.core import validate_api_call, validate
from flex.exceptions import ValidationError


class ValidationUtil(object):

    swagger_schema = None

    def __init__(self, fileutil):
        self.fileutil = fileutil

    def __call__(self, schema, response, *args, **kwargs):
        result = list()
        for attr in self.__dir__():
            if attr.startswith("validate"):
                validation_error = getattr(self, attr)(schema, response)
                if validation_error:
                    result.append(validation_error)
        return result

    def _load(self, api_level):
        self.swagger_schema = self.fileutil.load_validation_schema(api_level)

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


