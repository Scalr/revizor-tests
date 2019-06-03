import logging
import time
import uuid
import os
import json
from datetime import datetime

import pytest
from _pytest.fixtures import FixtureRequest
from paramiko.ssh_exception import NoValidConnectionsError

from revizor2 import CONF
from revizor2.api import Farm, IMPL
from revizor2.cloud import Cloud
from revizor2.testenv import TestEnv
from revizor2.utils import wait_until

import scalarizr.lib.farm as lib_farm
import scalarizr.lib.server as lib_server


LOG = logging.getLogger(__name__)

pytest_plugins = [
    'scalarizr.plugins.revizor',
    'scalarizr.plugins.reporter',
    'scalarizr.plugins.ordering',
    'scalarizr.plugins.surefire'
]


@pytest.fixture(scope='session', autouse=True)
def testenv(request) -> TestEnv:
    LOG.info('Preparing TestEnv')
    te = None
    new_te = False
    if CONF.scalr.te_id:
        te = TestEnv(te_id=CONF.scalr.te_id)
    elif CONF.scalr.branch:
        LOG.info('Run test in Test Env with branch: %s' % CONF.scalr.branch)
        # TODO: merge common TE creation process with UI
        # and implement method to bypass nginx welcome page
        notes = 'Revizor Scalarizr tests'
        if CONF.credentials.scalr.accounts.default.username:
            notes += (' <%s>' % CONF.credentials.scalr.accounts.default.username)
        te = TestEnv.create(branch=CONF.scalr.branch, notes=notes)
        LOG.info(f'TestEnv for tests created: {te.te_id}')
        for _ in range(5):
            try:
                services = te.get_service_status()
                if all(service['state'] == 'RUNNING' for service in services):
                    break
                time.sleep(3)
            except NoValidConnectionsError:
                time.sleep(3)
        CONF.scalr.te_id = te.te_id
        new_te = True
    try:
        yield te
    finally:
        if te \
          and CONF.feature.stop_farm \
          and (new_te and request.session.testsfailed == 0 or request.config.getoption('--te-remove')):
            # Removing TestEnv only if it was created by test and no tests failed
            # or when --te-remove flag was given
            te.destroy()


@pytest.fixture(scope="session", autouse=True)
def upload_scripts(testenv):
    if CONF.scalr.te_id:
        LOG.info("Uploading scripts to test env")
        existing_scripts = [script['name'] for script in IMPL.script.list()]
        path_to_scripts = CONF.main.home / 'fixtures' / 'testusing' / 'scripts'
        upload_counter = 0
        for _, script_path in enumerate(os.listdir(str(path_to_scripts))):
            LOG.debug(f'Upload script {script_path}')
            with (path_to_scripts / script_path).open(mode='r') as f:
                script_params = json.load(f)
            if script_params['name'] in existing_scripts:
                LOG.info(f"Script '{script_params['name']}' already exists")
                continue
            script_type = script_params.get('type', 'scalr')
            if script_type == 'git':
                repo_params = script_params['credentials']
                if repo_params['auth_type'] == 'ssh' and 'ssh_key' not in repo_params.keys():
                    repo_params['ssh_key'] = CONF.credentials.github.ssh_key_path
                script_params['repo_id'] = IMPL.services.git.create_repository(**repo_params)['id']
            getattr(IMPL.script, f"create_{script_type}_script")(**script_params)
            LOG.info(f"Script '{script_params['name']}' successfully uploaded")
            upload_counter += 1
        LOG.info(f"Total number of uploaded scripts: {upload_counter}")


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
def farm(request: FixtureRequest) -> Farm:
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
        failed_count = request.session.testsfailed
        LOG.info('Failed tests: %s' % failed_count)
        if (failed_count == 0 and CONF.feature.stop_farm) or (CONF.feature.stop_farm and CONF.scalr.te_id):
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
        LOG.info('Farm finalize complete')
