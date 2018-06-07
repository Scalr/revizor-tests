# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import json
import pytest

from pathlib import Path


class FileNotFoundError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class FileFixture(object):

    def __init__(self, request):
        self._request = request
        self._path = request.fspath.dirpath()
        self.base_working_dir = Path(self._path.strpath).joinpath('../../')

    def get_specification_by_test_name(self, name, splitter=None):
        splitter = splitter or "_"
        spec_file_pattern = "*%s*.json" % name.split(splitter)[-1]
        spec_path = self._find_dir(
            self.base_working_dir.joinpath('specifications'),
            name)
        spec_file = list(spec_path.glob(spec_file_pattern))
        if spec_file:
            with spec_path.joinpath(spec_file[-1]).open() as spec:
                return json.load(spec)
        raise FileNotFoundError('File by mask {} not found in {}'.format(
            spec_file_pattern,
            spec_path.as_posix()
        ))

    def _find_dir(self, base_path, pattern, splitter=None):
        splitter = splitter or "_"
        splitted_path = pattern.split(splitter)
        while splitted_path:
            path = base_path.joinpath(*splitted_path)
            if path.exists() and path.is_dir():
                return path
            del(splitted_path[-1])
        raise PathNotFoundError(
            'Path by pattern {} not found in {}!'.format(
                pattern,
                base_path.as_posix()))




@pytest.fixture
def fileutil(request):
    return FileFixture(request)
