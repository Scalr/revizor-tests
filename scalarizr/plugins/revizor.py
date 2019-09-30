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
    config.addinivalue_line('markers',
                            'chef: test verifies Chef orchestration.')
    config.addinivalue_line('markers',
                            'efs:  mark test as related to storages with elastic file system.')


def pytest_addoption(parser):
    group = parser.getgroup('revizor', 'revizor tests options', after='general')
    group.addoption('--te-id',
                    action='store',
                    default=None,
                    help='Use already created TestEnv.')
    group.addoption('--scalr-branch',
                    action='store',
                    default=None,
                    help='Scalr branch to instantiate test environment from.')
    group.addoption('--branch',
                    action='store',
                    default='master',
                    help='Scalarizr branch for farmrole.')
    group.addoption('--to-branch',
                    action='store',
                    default=None,
                    help='Scalarizr alternative branch for some tests') #TODO: Investigate this and remove
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
                    default='ubuntu1604',
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
    branch = session.config.getoption('--branch')
    to_branch = session.config.getoption('--to-branch')

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
    if branch:
        CONF.feature.branch = branch
    if to_branch:
        CONF.feature.to_branch = to_branch
    if session.config.getoption('--no-stop-farm'):
        CONF.feature.stop_farm = False
    if branch:
        CONF.feature.branch = branch


def pytest_collection_modifyitems(session, config: Config, items: tp.List[Function]):
    """Filter out tests according to @pytest.mark.run_only_if marker"""
    remaining = []
    deselected = []
    env = {
        'platform': CONF.feature.platform.name,
        'dist': CONF.feature.dist.id,
        'family': CONF.feature.dist.family
    }
    for item in items:
        conditions = item.get_closest_marker(name='run_only_if')
        if not conditions:
            remaining.append(item)
            continue
        for cond_name, cond_values in conditions.kwargs.items():
            pass_list, break_list = [], []
            if isinstance(cond_values, str):
                cond_values = [cond_values]

            for v in cond_values:
                if v.startswith('!'):
                    break_list.append(v.strip('!'))
                else:
                    pass_list.append(v)
            if (pass_list and env[cond_name] not in pass_list) or (break_list and env[cond_name] in break_list):
                if item not in deselected:
                    deselected.append(item)
                if item in remaining:
                    remaining.remove(item)
                break
            else:
                if item not in remaining:
                    remaining.append(item)
    #FIXME: modify to https://stackoverflow.com/questions/32247736/mark-test-as-skipped-from-pytest-collection
    # -modifyitems
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining
