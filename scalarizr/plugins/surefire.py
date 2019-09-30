import os
import json
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
        self._revizor_url = os.environ.get('REVIZOR_URL', 'https://revizor.scalr-labs.com')
        self._testcase_ids = {}
        self._module_ids = {}

    def log_test_status(self, item, status: str, exception: str = None):
        body = {
            'status': status
        }
        if exception:
            body['error_text'] = exception
        requests.patch(f'{self._revizor_url}/api/tests/cases/{self._testcase_ids[item.name]}',
                       json=body, headers={'Authorization': f'Token {self._token}'})

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Function, call: CallInfo) -> TestReport:
        become = yield
        report = become.get_result()

        if call.when == 'setup' and report.outcome == 'passed':
            self.log_test_status(item, 'STARTED')
        elif call.when in ('setup', 'call') and report.outcome == 'failed':
            self.log_test_status(item, 'FAILED', str(report.longrepr))
        elif call.when == 'call' and report.outcome == 'passed':
            self.log_test_status(item, 'COMPLETED')
        return report

    def pytest_collection_finish(self, session):
        modules = []
        for i in session.items:
            if i.get_closest_marker('skip'):
                continue
            module = i.listchain()[2]
            module_path = module.fspath.strpath.split(BASE_PATH)[1][1:]
            if module_path not in modules:
                modules.append(module_path)
        for m in modules:
            LOG.info(f'Create module in revizor with name {m} for test run {self._testsuite_id}')
            resp = requests.post(f'{self._revizor_url}/api/tests/modules',
                                 json={
                                     'name': m,
                                     'test_run': self._testsuite_id
                                 }, headers={'Authorization': f'Token {self._token}'})
            if resp.status_code != 201:
                raise AssertionError(f'Can\'t create module in revizor error {resp.text}')
            self._module_ids[m] = resp.json()['id']
        for i in session.items:
            if i.get_closest_marker('skip'):
                continue
            module_name = i.listchain()[2].fspath.strpath.split(BASE_PATH)[1][1:]
            module_id = self._module_ids[module_name]
            name = f'{i.parent.parent.name}::{i.name}'  # FIXME: Cases without class and better check for class
            doc = i.obj.__doc__
            resp = requests.post(f'{self._revizor_url}/api/tests/cases',
                                 json={
                                     'module': module_id,
                                     'name': name,
                                     'description': doc
                                 }, headers={'Authorization': f'Token {self._token}'})
            self._testcase_ids[i.name] = resp.json()['id']
