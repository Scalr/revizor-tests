import time

import pytest
from paramiko.ssh_exception import NoValidConnectionsError

from selene.api import browser, s
from selene.conditions import visible

from revizor2.conf import CONF
from revizor2.fixtures import resources
from revizor2.testenv import TestEnv

from pages.login import LoginPage
from pages.terraform.dashboard import TerraformEnvDashboard


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


@pytest.fixture(scope="session")
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


@pytest.fixture()
def tf_dashboard(testenv):
    browser.open_url(f'https://{testenv.te_id}.test-env.scalr.com')
    s('#loading').should_not_be(visible, timeout=20)
    url = browser.driver().current_url
    if '/dashboard' in url:
        return TerraformEnvDashboard()
    else:
        login_page = LoginPage()
        login_page.set_username(CONF.credentials.testenv.accounts.terraform.username)
        login_page.set_password(CONF.credentials.testenv.accounts.terraform.password)
        return login_page.submit()
