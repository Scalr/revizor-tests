# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import re

import pytest
import requests

from pathlib import Path
from urllib.parse import urlunparse

from api.utils.exceptions import PathNotFoundError


@pytest.fixture(scope="session", autouse=True)
def working_dir(request):
    work_dir = Path("/tmp/scalr_api")
    if not work_dir.exists():
        work_dir.mkdir()
    request.config.option.working_dir = work_dir
    return work_dir


@pytest.fixture(scope="session")
def fileutil(request):
    return FileFixture(request)


class FileFixture(object):

    _schemas_uri_suffix = "api/{api_level}.v1beta0.yml"
    _schemas_cache = "specifications"

    def __init__(self, request):
        self._request = request
        self.root_dir = Path(request.config.rootdir.strpath)
        self.working_dir = request.config.option.working_dir
        self._api_credentials = None

    @property
    def api_credentials(self):
        if not self._api_credentials:
            self._api_credentials = getattr(self._request.config, 'api_environment')
        return self._api_credentials

    def _get_swagger_definitions_from_url(self, api_level, dst):
        if not dst.exists():
            dst.mkdir(parents=True)
        url = urlunparse((
            self.api_credentials['schema'],
            self.api_credentials['host'],
            self._schemas_uri_suffix.format(api_level=api_level),
            '', '', ''))
        resp = requests.get(url=url, allow_redirects=True)
        resp.raise_for_status()
        print(resp.headers['Content-Disposition'])
        fname = re.findall("filename=([\w\W]+)$", resp.headers['Content-Disposition'])[0]
        dst = dst.joinpath(fname)
        dst.write_bytes(resp.content)
        return dst

    def get_swagger_difinitions(self, pattern):
        path = self.working_dir.joinpath(self._schemas_cache)
        search_criteria = dict(
            mask="*{}*.yaml".format(pattern),
            path=path)
        try:
            swagger_def = self._find(**search_criteria)
        except (PathNotFoundError, FileNotFoundError):
            swagger_def = self._get_swagger_definitions_from_url(pattern, path)
        return swagger_def.as_posix()

    def _find(self, path, mask):
        if not path.exists():
            raise PathNotFoundError("Path {} doe's not exists".format(path.as_posix()) )
        result = list(path.rglob(mask))
        if not result:
            raise FileNotFoundError("File by mask {} not recursively found in {}".format(
                mask,
                path.as_posix()
            ))
        return result[0]
