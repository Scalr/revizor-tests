import typing as tp

from _pytest.config import Config
from _pytest.main import Session
from _pytest.python import Function

from revizor2 import CONF
from revizor2.consts import Platform, Dist


def pytest_configure(config):
    config.addinivalue_line('markers',
                            'platform(*platforms): specify allowed clouds for test.')
    config.addinivalue_line('markers',
                            'boot: mark test as related to server bootstrap.')
    config.addinivalue_line('markers',
                            'szradm: mark test as related to SzrAdm.')


def pytest_addoption(parser):
    parser.addoption('--te-id', action='store', default=None)
    parser.addoption('--farm-id', action='store', default=None)
    parser.addoption('--platform', action='store', default=None)
    parser.addoption('--dist', action='store', default=None)


def pytest_sessionstart(session: Session):
    te_id = session.config.getoption('--te-id')
    farm_id = session.config.getoption('--farm-id')
    platform = session.config.getoption('--platform')
    dist = session.config.getoption('--dist')
    if te_id:
        CONF.scalr.te_id = te_id
    if farm_id:
        CONF.main.farm_id = farm_id
    if platform:
        CONF.feature.platform = Platform(driver=platform)
    if dist:
        CONF.feature.dist = Dist(dist_name=dist)


def pytest_collection_modifyitems(session, config: Config, items: tp.List[Function]):
    remaining = []
    deselected = []
    for item in items:
        platforms_mark = item.get_closest_marker(name='platform')
        if platforms_mark:
            platforms = platforms_mark.args
            if CONF.feature.platform.name not in platforms:
                deselected.append(item)
                continue
        remaining.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining
