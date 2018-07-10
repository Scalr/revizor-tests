# coding: utf-8
"""
Created on 18.06.18
@author: Eugeny Kurkovich
"""
import re
import os
import json

import pytest

from six import string_types

from pyswagger import App
from box import Box

from api.plugins.filefixture import FileNotFoundError, ValidationUtil
from api.utils.session import ScalrApiSession

RELATIVE_CONF_PATH = "conf/environment.json"


class AppMixin(object):

    app = None

    app_tree = None

    app_root = "/api/v1beta0/{api_level}/"

    _app_level = None

    _app_session = None

    _app_checker = None

    def __init__(self, request, fileutil):
        self._app_level = getattr(request.module, "app_level", None)
        self._app_checker = ValidationUtil(request)
        schema = fileutil.get_validation_schema(self._app_level)
        self.app = App.create(schema)
        self.app_root = self.__class__.app_root.format(api_level=self._app_level)
        self.app_tree = Box(AppMixin._parse_root(self.app.root.paths.keys()))

    @staticmethod
    def _parse_root(root):
        r = dict()
        for path in root:
            path_items = re.sub(r"[\{\}]", "", path).split("/")
            key = os.path.join(*filter(None, path_items))
            r[key] = path
        return r


class SessionMixin(AppMixin):

    def __init__(self, request, fileutil, credentials):
        super(SessionMixin, self).__init__(request, fileutil)
        self._app_session = ScalrApiSession(**credentials)

    def __getattr__(self, name):
        def _handler(*args, **kwargs):
            if len(args) == 1:
                if not isinstance(args[0], string_types):
                    raise ValueError('Request args mismatch')
            else:
                raise TypeError('Request session expected at most 1 argument, got {0}'.format(len(args)))
            kwargs['method'] = name
            return self._execute_request(*args, **kwargs)
        return _handler

    def close(self):
        self._app_session.close()

    def _prepare_path(self, path):
        path_items = filter(None, path.split(self.app_root)[1].split('/'))
        path = os.path.join(*path_items)
        return getattr(self.app_tree, path)

    def _execute_request(self, endpoint, method, params, filters=None, body=None):
        try:
            endpoint = self._prepare_path(endpoint)
            spec = Box(self.app.s(endpoint).dump())
        except Exception as e:
            raise e.__class__("Endpoint {} doe's not exists".format(endpoint))
        request_kwargs = dict(
            method=method,
            endpoint=os.path.join(self.app_root, *filter(None, endpoint.split('/'))),
            params=params,
            body=body,
            filters=filters
        )
        resp = self._app_session.request(
            **self._app_checker.validate_request(
                spec,
                request_kwargs))
        return resp


@pytest.fixture(scope='module', autouse=True)
def app_session(request, fileutil, get_credentials):
    session = SessionMixin(request, fileutil, get_credentials)
    return session


@pytest.fixture(scope='module')
def get_credentials(fileutil):
    path = fileutil.root_dir.joinpath(RELATIVE_CONF_PATH)
    if not path.exists():
        raise FileNotFoundError(
            "Credentials is unavailable, {} not found".format(path.as_poasix()))
    with path.open() as f:
        return json.load(f)

