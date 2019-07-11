import os
import json
import pathlib

import requests
import pytest
from _pytest.config import Config
from _pytest.python import Function
from _pytest.runner import CallInfo
from _pytest.reports import TestReport


BASE_PATH = str(pathlib.Path(__file__).parent.parent.parent)


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
        if call.when == 'setup':
            self.log_test_status(item, 'STARTED')
        elif call.when == 'call':
            status = 'COMPLETED'
            if report.outcome == 'failed':
                status = 'FAILED'
            self.log_test_status(item, status, str(report.longrepr))
        return report

    def pytest_collection_modifyitems(self, session, config, items):
        modules = []
        for i in items:
            module = i.listchain()[2]
            module_path = module.fspath.strpath.split(BASE_PATH)[0]
            if module_path not in modules:
                modules.append(module_path)
        for m in modules:
            resp = requests.post(f'{self._revizor_url}/api/tests/modules',
                                 json={
                                     'name': m,
                                     'test_run': self._testsuite_id
                                 }, headers={'Authorization': f'Token {self._token}'})
            self._module_ids[m] = resp.json()['id']
        for i in items:
            module_name = i.listchain()[2].fspath.strpath.split('revizor-tests')[1][1:]
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
