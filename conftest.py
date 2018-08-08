import logging

import pytest

from revizor2 import CONF
from revizor2.consts import Platform

LOG = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption('--te-id', action='store', default=None)
    parser.addoption('--platform', action='store', default=None)
    parser.addoption('--dist', action='store', default=None)


@pytest.fixture(scope='session', autouse=True)
def prepare_config(request):
    te_id = request.config.getoption('--te-id')
    platform = request.config.getoption('--platform')
    dist = request.config.getoption('--dist')
    if te_id:
        CONF.scalr.te_id = te_id
    if platform:
        CONF.feature.platform = Platform(driver=platform)
    if dist:
        CONF.feature.dist = dist
