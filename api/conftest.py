# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""

import os
import json
import pytest

RELATIVE_CONF_PATH = 'conf/environment.json'

pytest_plugins = [
    "api.plugins.filefixture",
    "api.plugins.session",
]


@pytest.fixture(scope="session", autouse=True)
def setup_api_credentials(fileutil):
    credentials_path = fileutil.root_dir.joinpath(RELATIVE_CONF_PATH)
    if credentials_path.exists():
        with credentials_path.open() as f:
            credentials = json.load(f)
            os.environ.update(
                dict(API_CREDENTIALS=json.dumps(credentials))
            )



