import os
import pathlib
import logging

import requests
import pytest
from _pytest.config import Config
from _pytest.python import Function
from _pytest.runner import CallInfo
from _pytest.reports import TestReport

BASE_PATH = str(pathlib.Path(__file__).parent.parent.parent)

LOG = logging.getLogger(__name__)


def pytest_addoption(parser):
    group = parser.getgroup('surefire', 'surefire tests options', after='revizor')
    group.addoption('--report-surefire',  # TODO: Think about option name
                    action='store_true',
                    dest='report_surefire',
                    help='Notify Surefire about tests')


@pytest.mark.trylast
def pytest_configure(config: Config):
    if config.getoption('--report-surefire'):
        plugin = SurefireRESTReporter(config)
        config.pluginmanager.register(plugin, 'surefirereporter')


class SurefireRESTReporter:
    def __init__(self, config: Config):
        self._config = config
        self._token = os.environ.get('REVIZOR_API_TOKEN')
        self._testsuite_id = os.environ.get('REVIZOR_TESTINSTANCE_ID')
        self._revizor_url = os.environ.get('REVIZOR_URL', 'https://revizor.scalr-labs.net')
        self._testcase_ids = {}
        self._module_ids = {}
        self._session = None

    @property
    def req(self):
        if not self._session:
            self._session = requests.Session()
            self._session.headers = {
                'Authorization': f'Token {self._token}'
            }
        return self._session

    def log_test_status(self, item: Function, status: str, exception: str = None):
        body = {
            'status': status
        }
        if exception:
            body['error_text'] = exception
        self.req.patch(f'{self._revizor_url}/api/tests/cases/{self._testcase_ids[item.name]}', json=body)

    def upload_test_file(self, item: Function, file_path: str):
        resp = self.req.post(f'{self._revizor_url}/api/tests/cases/{self._testcase_ids[item.name]}/upload',
                             files={'obj': open(file_path, 'rb')})
        LOG.debug(f'Response from file upload: {resp.text}')

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Function, call: CallInfo) -> TestReport:
        become = yield
        report = become.get_result()

        if call.when == 'setup' and report.outcome == 'passed':
            self.log_test_status(item, 'STARTED')
        elif call.when == 'setup' and report.outcome == 'skipped':
            self.log_test_status(item, 'SKIPPED', str(report.longrepr[2]))
        elif call.when in ('setup', 'call') and report.outcome == 'failed':
            self.log_test_status(item, 'FAILED', str(report.longrepr))
        elif call.when == 'call' and report.outcome == 'passed':
            self.log_test_status(item, 'COMPLETED')
        elif call.when == 'teardown' and report.outcome == 'failed':
            f = getattr(item.session, 'screenshot_path', None)
            if f:
                LOG.debug(f'Upload file: f')
                self.upload_test_file(item, f)
        return report

    def pytest_collection_finish(self, session):
        modules = []
        for i in session.items:
            module = i.listchain()[2]
            module_path = module.fspath.strpath.split(BASE_PATH, 1)[1]
            if module_path not in modules:
                modules.append(module_path)
        for m in modules:
            LOG.info(f'Create module in revizor with name {m} for test run {self._testsuite_id}')
            resp = self.req.post(f'{self._revizor_url}/api/tests/modules',
                                 json={
                                     'name': m,
                                     'test_run': self._testsuite_id
                                 })
            if resp.status_code != 201:
                raise AssertionError(f'Can\'t create module in revizor error {resp.text}')
            self._module_ids[m] = resp.json()['id']
        for i in session.items:
            module_name = i.listchain()[2].fspath.strpath.split(BASE_PATH, 1)[1]
            module_id = self._module_ids[module_name]
            name = f'{i.parent.parent.name}::{i.name}'  # FIXME: Cases without class and better check for class
            doc = i.obj.__doc__
            resp = self.req.post(f'{self._revizor_url}/api/tests/cases',
                                 json={
                                     'module': module_id,
                                     'name': name,
                                     'description': doc
                                 })
            self._testcase_ids[i.name] = resp.json()['id']
