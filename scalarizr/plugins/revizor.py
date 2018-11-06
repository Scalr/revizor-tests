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
    config.addinivalue_line('markers',
                            'partition: mark test as related to volume partitioning.')
    config.addinivalue_line('markers',
                            'storages: mark test as related to storages.')
    config.addinivalue_line('markers',
                            'fstab: mark test as related to fstab.')
    config.addinivalue_line('markers',
                            'reboot: marked test reboots the server.')
    config.addinivalue_line('markers',
                            'scripting: test executes scripts on the server.')
    config.addinivalue_line('markers',
                            'restart: test restarts server agent.')
    config.addinivalue_line('markers',
                            'event: tests Scalr events.')
    config.addinivalue_line('markers',
                            'restartfarm: test restarts farm.')
    config.addinivalue_line('markers',
                            'failedbootstrap: server fails on bootstrap in test.')


def pytest_addoption(parser):
    group = parser.getgroup('revizor', 'revizor tests options', after='general')
    group.addoption('--te-id',
                    action='store',
                    default=None,
                    help='Use already created TestEnv.')
    group.addoption('--scalr-branch',
                    action='store',
                    default='None',
                    help='Scalr branch to instantiate test environment from.')
    group.addoption('--farm-id',
                    action='store',
                    default=None,
                    help='Farm to use for tests. If not set, temporary Farm will be created.')
    group.addoption('--platform',
                    action='store',
                    default=None,
                    choices=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'],
                    help='Cloud platform to launch tests on')
    group.addoption('--dist',
                    action='store',
                    default=None,
                    help='OS distro to be tested.')
    group.addoption('--no-stop-farm',
                    action='store_true',
                    default=False,
                    help='Leave test Farm running after the tests.')
    group.addoption('--te-remove',
                    action='store_true',
                    default=False,
                    help='Destroy TestEnv even when some tests fail.')


def pytest_sessionstart(session: Session):
    te_id = session.config.getoption('--te-id')
    scalr_branch = session.config.getoption('--scalr-branch')
    farm_id = session.config.getoption('--farm-id')
    platform = session.config.getoption('--platform')
    dist = session.config.getoption('--dist')
    if te_id:
        CONF.scalr.te_id = te_id
    if scalr_branch:
        CONF.scalr.branch = scalr_branch
    if farm_id:
        CONF.main.farm_id = farm_id
    if platform:
        CONF.feature.platform = Platform(driver=platform)
    if dist:
        CONF.feature.dist = Dist(dist_name=dist)
    if session.config.getoption('--no-stop-farm'):
        CONF.feature.stop_farm = False


def pytest_collection_modifyitems(session, config: Config, items: tp.List[Function]):
    """Filter out tests according to @pytest.mark.platform marker"""
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
