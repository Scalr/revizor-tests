import logging
import uuid
from datetime import datetime

import pytest

from revizor2 import CONF
from revizor2.api import Farm, IMPL
from revizor2.cloud import Cloud
import scalarizr.lib.farm as lib_farm
import scalarizr.lib.server as lib_server
from revizor2.utils import wait_until

LOG = logging.getLogger(__name__)

pytest_plugins = [
    'scalarizr.plugins.revizor',
    'scalarizr.plugins.reporter',
    'scalarizr.plugins.ordering'
]


@pytest.fixture(scope='session')
def cloud() -> Cloud:
    LOG.info('Initialize a Cloud object')
    return Cloud()


@pytest.fixture(scope='class')
def context() -> dict:
    return {}


@pytest.fixture(scope='class')
def servers() -> dict:
    return {}


@pytest.fixture(scope='class', autouse=True)
def initialize_test(context: dict, cloud: Cloud):
    test_start_time = datetime.now()
    test_id = uuid.uuid4().hex
    context['test_start_time'] = test_start_time
    context['test_id'] = test_id
    LOG.info(f'Test ID: "{test_id}", started at {test_start_time}')


@pytest.fixture(scope='class')
def farm():
    if CONF.main.farm_id is None:
        LOG.info('Farm ID not set, create a new farm for test')
        test_farm = Farm.create(f'tmprev-{datetime.now().strftime("%d%m%H%M%f")}',
                                'Revizor farm for tests\n'
                                f'RV_BRANCH={CONF.feature.branch}\n'
                                f'RV_PLATFORM={CONF.feature.platform.name}\n'
                                f'RV_DIST={CONF.feature.dist.dist}\n')
        CONF.main.farm_id = test_farm.id
    else:
        LOG.info(f'Farm ID is set in config, use it: {CONF.main.farm_id}')
        test_farm = Farm.get(CONF.main.farm_id)
    lib_farm.clear(test_farm)
    LOG.info(f'Returning test farm: {test_farm.id}')
    try:
        yield test_farm
    finally:
        LOG.info('Clear and stop farm...')
        test_farm.terminate()
        IMPL.farm.clear_roles(test_farm.id)
        if test_farm.name.startswith('tmprev'):
            LOG.info('Delete working temporary farm')
            try:
                LOG.info('Wait all servers in farm terminated before delete')
                wait_until(lib_server.farm_servers_state,
                           args=(test_farm, 'terminated'),
                           timeout=1800,
                           error_text='Servers in farm not terminated too long')
                test_farm.destroy()
            except Exception as e:
                LOG.warning(f'Farm cannot be deleted: {str(e)}')
