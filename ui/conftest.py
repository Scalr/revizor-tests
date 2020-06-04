import re
import time
import logging
import typing as tp

import pytest
from _pytest.fixtures import FixtureRequest

import requests
from selenium import webdriver
from selene.api import s, be
from selene.support.shared import config, browser

from revizor2.conf import CONF
from revizor2.fixtures import resources
from revizor2.testenv import TestEnv

from ui.pages.login import LoginPage
from ui.pages.admin.dashboard import AdminDashboard
from ui.pages.account.dashboard import AccountDashboard
from ui.pages.classic.dashboard import ClassicEnvDashboard
from ui.pages.terraform.dashboard import TerraformEnvDashboard


LOG = logging.getLogger(__name__)


def pytest_addoption(parser):
    group = parser.getgroup("revizor selenium", after="general")
    group.addoption(
        "--te-remove",
        dest="te_remove",
        action="store_true",
        default=False,
        help="Destroy TestEnv even when some tests fail.",
    )
    group.addoption(
        "--page-load-timeout",
        dest="load_timeout",
        action="store",
        default=30,
        type=int,
        help="Seconds to wait page load",
    )
    group.addoption(
        "--te-id",
        "--test-environment-id",
        dest="te_id",
        action="store",
        help="Scalr test environment id to use existing env",
        default=None,
    )
    group.addoption(
        "--scalr-branch",
        "--scalr-branch",
        dest="scalr_branch",
        action="store",
        help="Scalr test environment branch",
        default="master",
    )
    group.addoption(
        "--browser",
        dest="selenium_browser",
        action="store",
        default="chrome79",
        help="Browser type and version (example: chrome77, firefox50). Version work only with remote driver",
    )

    group.addoption(
        "--grid-address",
        dest="selenium_grid_address",
        action="store",
        default="",
        help="Remote selenium grid address",
    )


@pytest.fixture(scope="session", autouse=True)
def testenv(request: FixtureRequest) -> TestEnv:
    """Creates and yeild revizor TestEnv container.
       Destroys container after all tests in TestClass were executed,
       unless some of the tests failed.
    """
    te_id = request.config.getoption("te_id")
    te_remove = request.config.getoption("te_remove")
    if te_id:
        container = TestEnv(te_id)
    else:
        container = TestEnv.create(
            branch=request.config.getoption("scalr_branch"), notes="Selenium test container"
        )
        for _ in range(24):
            LOG.debug(f"Check container {container.url} return Scalr page")
            resp = requests.get(container.url)
            if "Scalr CMP" in resp.text:
                break
            time.sleep(5)
        else:
            raise TimeoutError(f"Container {container.url} not return Scalr CMP page")
        # for _ in range(10):
        #     try:
        #         services = container.get_service_status()
        #         if all(service['state'] == 'RUNNING' for service in services):
        #             break
        #         time.sleep(3)
        #     except NoValidConnectionsError:
        #         time.sleep(3)
    CONF.scalr.te_id = container.te_id
    yield container
    if (request.node.session.testsfailed == 0 and not te_id) or te_remove:
        container.destroy()


@pytest.fixture(scope="session", autouse=True)
def setup_driver(request: FixtureRequest, testenv: TestEnv):
    LOG.debug("Setup webdriver fixture")
    remote_addr = request.config.getoption("selenium_grid_address")
    br = re.findall(r"([a-zA-Z]+)(\d+)", request.config.getoption("selenium_browser"))

    if br:
        browser_name, browser_version = br[0]
    else:
        browser_name = request.config.getoption("selenium_browser")
        browser_version = None
    browser_name = browser_name.lower()

    LOG.debug(f"Browser settings: {browser_name}:{browser_version}")

    if remote_addr:
        LOG.debug(f"Connect to remote webdriver {remote_addr}")
        driver = webdriver.Remote(
            command_executor=f"http://{remote_addr}:4444/wd/hub",
            desired_capabilities={
                "browserName": browser_name,
                "version": f"{browser_version}.0",
                "enableVNC": True,
                "enableVideo": False,
            },
            keep_alive=True,
        )
        LOG.debug("Connect successfully")
        driver.maximize_window()
        LOG.debug("Save driver to selene")
        config.driver = driver
    else:
        config.browser_name = browser_name
    yield
    browser.quit()


@pytest.fixture(scope="function")
def mock_ssmtp(request: FixtureRequest):
    if hasattr(request.instance, "container"):
        container = request.instance.container
    else:
        raise AttributeError("Test instance has no TestEnv associated with it!")
    ssh = container.get_ssh()
    ssh.run("rm -f /opt/scalr-server/libexec/mail/ssmtp")
    ssmtp_script = resources("scripts/ssmtp")
    container.put_file(ssmtp_script.fp.name, "/opt/scalr-server/libexec/mail/ssmtp")
    ssh.run("chmod 777 /opt/scalr-server/libexec/mail/ssmtp")


@pytest.fixture()
def tf_dashboard(
    testenv: TestEnv,
) -> tp.Union[AdminDashboard, AccountDashboard, TerraformEnvDashboard, ClassicEnvDashboard]:
    browser.open_url(f"https://{testenv.te_id}.test-env.scalr.com")
    s("#loading").should(be.not_.visible, timeout=20)
    url = browser.driver().current_url
    if "/dashboard" in url:
        return TerraformEnvDashboard()
    else:
        login_page = LoginPage()
        login_page.set_idp_provider("scalr")
        login_page.set_username(CONF.credentials.testenv.accounts.terraform.username)
        login_page.set_password(CONF.credentials.testenv.accounts.terraform.password)
        return login_page.submit()
