import uuid
import os
import time
from pathlib import Path

import pytest
from paramiko.ssh_exception import NoValidConnectionsError


from revizor2.testenv import TestEnv
from revizor2.fixtures import resources


def pytest_addoption(parser):
    group = parser.getgroup("docker controller", "fatmouse", after="general")
    group.addoption(
        "--te-id", action="store", default=None, help="Use already created TestEnv."
    )
    group.addoption(
        "--te-remove", action="store", default=None, help="Destroy TestEnv even when some tests fail."
    )
    group.addoption(
        "--debug-mode", action="store", default=None, help="Show log messages as they appear. Set message level (DEBUG, INFO, WARNING and so on)."
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
    te_id = request.config.getoption("--te-id")
    te_remove = request.config.getoption("--te-remove")
    if te_id:
        container = TestEnv(te_id)
    else:
        container = TestEnv.create(branch='master', notes='Selenium test container')
        for _ in range(5):
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
