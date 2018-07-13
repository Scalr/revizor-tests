# coding: utf-8
"""
Created on 18.06.18
@author: Eugeny Kurkovich
"""
import re
import os

import pytest

from six import string_types

from pyswagger import App
from box import Box

from api.plugins.validationfixture import ValidationUtil
from api.utils.session import ScalrApiSession


class AppMixin(object):

    app = None

    app_root = "/api/v1beta0/{api_level}/"

    _app_level = "user"

    _app_tree = None

    _app_session = None

    _app_checker = None

    def __init__(self, request, fileutil):
        self._app_level = getattr(
            request.module,
            "app_level",
            self.__class__._app_level)
        self._app_checker = ValidationUtil(fileutil)
        schema = fileutil.get_swagger_difinitions(self._app_level)
        self.app = App.create(schema)
        self.app_root = self.__class__.app_root.format(api_level=self._app_level)
        self._app_tree = Box(AppMixin._get_schema_tree(self.app.root.paths.keys()))

    @staticmethod
    def _get_schema_tree(root):
        r = dict()
        for path in root:
            path_items = re.sub(r"[\{\}]", "", path).split("/")
            key = os.path.join(*filter(None, path_items))
            r[key] = path
        return r

    def _path_form_endpoint(self, endpoint):
        path_items = filter(None, endpoint.split(self.app_root)[1].split('/'))
        endpoint = os.path.join(*path_items)
        return getattr(self._app_tree, endpoint)

    def get_request_spec_by_endpoint(self, endpoint):
        try:
            path = self._path_form_endpoint(endpoint)
            return Box(self.app.s(path).dump())
        except Exception:
            raise ValueError("Endpoint {} doe's not exists".format(endpoint))

    def parse_endpoint(self, endpoint):
        path = self._path_form_endpoint(endpoint)
        return os.path.join(self.app_root, *filter(None, path.split('/')))


class SessionMixin(AppMixin):

    def __init__(self, request, fileutil):
        super(SessionMixin, self).__init__(request, fileutil)
        self._app_session = ScalrApiSession(**fileutil.api_credentials)

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

    def close(self):
        self._app_session.close()

    def _execute_request(self, endpoint, method, params, filters=None, body=None):
        request_kwargs = dict(
            method=method,
            endpoint=self.parse_endpoint(endpoint),
            params=params,
            body=body,
            filters=filters
        )
        resp = self._app_session.request(
            **self._app_checker.validate_request(
                self.get_request_spec_by_endpoint(endpoint),
                request_kwargs))
        return resp


@pytest.fixture(scope='module', autouse=True)
def api(request, fileutil):
    session = SessionMixin(request, fileutil)
    request.addfinalizer(session.close)
    return session

