# coding: utf-8
"""
Created on 18.06.18
@author: Eugeny Kurkovich
"""
import re

import pytest
import requests

from six import string_types

from box import Box
from pyswagger import App
from flex.core import load as load_schema_from_file, validate as flex_validate_response

from api.utils.api_session import ScalrApiSession
from api.utils.helpers import serialize_platform_store
from api.utils.helpers import remove_empty_values
from api.utils.consts import APIParams
from api.utils.exceptions import ResponseValidationError


API_PREFIX = '/api/v1beta0/'
SPEC_FILE_FORMAT = '{}-autogenerated.yaml'


class AppSession(object):
    _app = None
    _app_tree = None
    _api_session = None

    successful_response_codes = dict(
        GET=[200],
        PATCH=[200],
        POST=[200, 201],
        DELETE=[204]
    )

    def __init__(self, request):
        self._request = request
        self.scopes = {
            'user': {
                'spec': None,
                'app': None,
                'tree': None,
                'flex': None
            },
            'global': {
                'spec': None,
                'app': None,
                'tree': None,
                'flex': None
            }
        }
        self.spec_path = request.config.working_dir / 'specs'

    def __getattr__(self, name):
        def _handler(*args, **kwargs):
            if len(args) == 1:
                if not isinstance(args[0], string_types):
                    raise ValueError('Request args mismatch')
            else:
                raise ValueError('Request session expected at most 1 argument, got {0}'.format(len(args)))
            kwargs['method'] = name
            return self._execute_request(*args, **kwargs)
        return _handler

    def get_swagger_specs(self, scope='user'):
        if self.scopes[scope]['spec'] is None:
            path = self.spec_path / SPEC_FILE_FORMAT.format(scope)
            if not path.exists():
                self.download_spec(scope)
            self.scopes[scope]['spec'] = path
        return self.scopes[scope]['spec']

    def download_spec(self, scope='user'):
        spec = requests.get(
            'http://{}/api/{}.v1beta0.yml'.format(self._request.config.api_environment['host'], scope)
        )
        if not self.spec_path.exists():
            self.spec_path.mkdir(parents=True)
        with open(self.spec_path / SPEC_FILE_FORMAT.format(scope), 'wb+') as sp:
            sp.write(spec.content)

    def get_endpoint(self, scope, endpoint):
        return '{}{}{}'.format(API_PREFIX, scope, self._get_endpoint_with_params(scope, endpoint))

    def _execute_request(self, endpoint, method, params=None, filters=None, body=None):
        scope = endpoint.split('/')[3]

        if scope not in self.scopes:
            self.scopes[scope] = {
                'app': None,
                'tree': None,
                'flex': None,
                'spec': None
            }

        if self.scopes[scope]['app'] is None:
            self.scopes[scope]['app'] = App.create(self.get_swagger_specs(scope).as_posix())
            self.scopes[scope]['tree'] = Box(self._get_schema_tree(scope))

        request_kwargs = dict(
            method=method,
            endpoint=self.get_endpoint(scope, endpoint),
            params=params or {},
            body=body,
            filters=filters
        )

        req_params = self.check_request_params(
            self._get_request_spec_by_endpoint(scope, endpoint),
            request_kwargs)

        if scope in ('account', 'user'):
            key_id = self._request.config.api_environment['config']['account_api']['id']
            secret_key = self._request.config.api_environment['config']['account_api']['secret']
        else:
            key_id = self._request.config.api_environment['config']['global_api']['id']
            secret_key = self._request.config.api_environment['config']['global_api']['secret']

        api = ScalrApiSession(
            host=self._request.config.api_environment['host'],
            secret_key_id=key_id,
            secret_key=secret_key
        )

        response = api.request(
            serializer=serialize_platform_store,
            **req_params
        )

        self.request_ok(response)

        if self._request.config.getoption("flex_validation"):
            self.validate_response(scope, response)
        return response

    def request_ok(self, response):
        response_successful_code = self.successful_response_codes.get(response.request.method)
        if response.status_code not in response_successful_code:
            raise ResponseValidationError('Response successful code not valid')

    def validate_response(self, scope, data):
        """
        :type: data: requests.Response
        :param data: raw requests.response

        :type: flex_validation: bool
        :param: flex_validation: Enabled response validation by flex

        :return: None or validation error
        """
        if not isinstance(data, requests.models.Response):
            raise ValueError('Not valid data format')

        if self.scopes[scope]['flex'] is None:
            self.scopes[scope]['flex'] = load_schema_from_file(self.get_swagger_specs(scope))

        data = data.json()
        flex_validate_response(
            self.scopes[scope]['flex'],
            data
        )

    @staticmethod
    def check_request_params(schema, req_params):
        method = req_params.get('method')
        params = req_params.get('params')
        filters = remove_empty_values(req_params.get('filters'))
        body = remove_empty_values(req_params.get('body'))
        required_params = []

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
        if 'parameters' in schema[http_meth]:
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

    def _get_schema_tree(self, scope):
        r = dict()
        for path in self.scopes[scope]['app'].root.paths.keys():
            key = re.sub(r"[\{\}]", "", path)
            r[key] = path
        return r

    def _get_endpoint_with_params(self, scope, endpoint):
        point = endpoint.split(API_PREFIX + scope)[-1]
        return getattr(self.scopes[scope]['tree'], point)

    def _get_request_spec_by_endpoint(self, scope, endpoint):
        try:
            path = self._get_endpoint_with_params(scope, endpoint)
            return Box(self.scopes[scope]['app'].s(path).dump())
        except Exception:
            raise ValueError("Endpoint {} does not exists".format(endpoint))


@pytest.fixture(scope='session', autouse=True)
def api(request):
    session = AppSession(request)
    return session
