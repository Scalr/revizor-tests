import os

import requests
import pytest
from _pytest.config import Config
from _pytest.python import Function
from _pytest.runner import CallInfo
from _pytest.reports import TestReport


def pytest_addoption(parser):
    group = parser.getgroup('surefire', 'surefire tests options', after='revizor')
    group.addoption('--report-surefire',  #TODO: Think about option name
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
        self._testcase_id = None

    def log_test_start(self, nodeid: str):
        resp = requests.post(f'{self._revizor_url}/api/tests/cases',
                             json={
                                 'test': self._testsuite_id,
                                 'name': nodeid
                             }, headers={'Authorization': f'Token {self._token}'})
        self._testcase_id = resp.json()['id']

    def log_test_status(self, nodeid: str, status: str, exception: str):
        status = {'passed': 'COMPLETED', 'failed': 'FAILED'}[status]
        requests.patch(f'{self._revizor_url}/api/tests/cases/{self._testcase_id}',
                       json={
                           'status': status,
                           'error_text': exception
                       }, headers={'Authorization': f'Token {self._token}'})

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Function, call: CallInfo) -> TestReport:
        become = yield
        report = become.get_result()
        if call.when == 'setup':
            self.log_test_start(item.nodeid)
        if (call.when == 'setup' and report.outcome == 'failed') or call.when == 'call':
            self.log_test_status(item.nodeid, report.outcome, str(report.longrepr))
        return report
