import os
import time
import uuid
from contextlib import contextmanager

import pytest
from paramiko.ssh_exception import NoValidConnectionsError

from revizor2.conf import CONF
from revizor2.fixtures import resources
from revizor2.testenv import TestEnv


def pytest_addoption(parser):
    group = parser.getgroup("revizor selenium", after="general")
    group.addoption(
        "--te-remove", dest="te_remove", action="store_true", default=False,
        help="Destroy TestEnv even when some tests fail."
    )
    group.addoption(
        "--page-load-timeout", dest="load_timeout", action="store", default=30, type=int,
        help="Seconds to wait page load",
    )
    group.addoption(
        "--te-id", "--test-environment-id", dest="te_id", action="store",
        help="Scalr test environment id to use existing env", default=None
    )


def pytest_runtest_makereport(item, call):
    """Saves screenshot when test fails and saves it in /ui directory.
    """
    if call.when == 'call' and call.excinfo:
        item.instance.driver.save_screenshot(os.getcwd() + "/ui/%s.png" % (item.name + '-' + str(uuid.uuid1())))


@pytest.fixture(scope="class")
def testenv(request):
    """Creates and yeild revizor TestEnv container.
       Destroys container after all tests in TestClass were executed,
       unless some of the tests failed.
    """
    te_id = request.config.getoption("te_id")
    te_remove = request.config.getoption("te_remove")
    if te_id:
        container = TestEnv(te_id)
    else:
        container = TestEnv.create(branch='master', notes='Selenium test container')
        for _ in range(10):
            try:
                services = container.get_service_status()
                if all(service['state'] == 'RUNNING' for service in services):
                    break
                time.sleep(3)
            except NoValidConnectionsError:
                time.sleep(3)
    yield container
    if (request.node.session.testsfailed == 0 and not te_id) or te_remove:
        container.destroy()


@pytest.fixture(scope="function")
def mock_ssmtp(request):
    if hasattr(request.instance, 'container'):
        container = request.instance.container
    else:
        raise AttributeError("Test instance has no TestEnv associated with it!")
    ssh = container.get_ssh()
    ssh.run("rm -f /opt/scalr-server/libexec/mail/ssmtp")
    ssmtp_script = resources('scripts/ssmtp')
    container.put_file(
        ssmtp_script.fp.name,
        '/opt/scalr-server/libexec/mail/ssmtp')
    ssh.run('chmod 777 /opt/scalr-server/libexec/mail/ssmtp')


@pytest.fixture
def selenium_driver(driver):
    """Provides patched Selenium driver instance.

    Changed:
        ``implicitly_wait``       -- added wrapper that saves last used ``time_to_wait`` value
                                     to ``implicit_time_to_wait`` instance attribute

    Added:
        ``implicit_time_to_wait`` -- instance attribute that holds last set ``time_to_wait`` value

        ``implicitly_wait_time``  -- context manager that allows to temporary change implicit wait time
                                     for a code block

    Usage::

        driver.implicitly_wait(10)
        LOG.debug('outer implicit_time_to_wait is %s' % driver.implicit_time_to_wait)
        with driver.implicitly_wait_time(3):
            LOG.debug('inner implicit_time_to_wait is %s' % driver.implicit_time_to_wait)

        > outer implicit_time_to_wait is 10
        > inner implicit_time_to_wait is 3
    """
    implicitly_wait_inner = driver.implicitly_wait

    def implicitly_wait_wrapper(self, time_to_wait):
        self.implicit_time_to_wait = time_to_wait
        implicitly_wait_inner(time_to_wait)

    @contextmanager
    def implicitly_wait_time(self, time_to_wait: int):
        prev_wait_time = getattr(self, 'implicit_time_to_wait', 0)
        self.implicitly_wait(time_to_wait)
        try:
            yield
        finally:
            self.implicitly_wait(prev_wait_time)

    driver.implicitly_wait = implicitly_wait_wrapper.__get__(driver, None)
    driver.implicitly_wait_time = implicitly_wait_time.__get__(driver, None)
    return driver


def pytest_sessionstart(session):
    session.config.admin_login = CONF.credentials.testenv.accounts.admin['username']
    session.config.admin_pass = CONF.credentials.testenv.accounts.admin['password']
