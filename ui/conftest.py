import uuid
import os
import time
from pathlib import Path

import pytest
from paramiko.ssh_exception import NoValidConnectionsError


from revizor2.testenv import TestEnv
from revizor2.fixtures import resources


def pytest_runtest_makereport(item, call):
    """Saves screenshot when test fails and saves it in /ui directory.
    """
    if call.when == 'call' and call.excinfo:
        item.instance.driver.save_screenshot(os.getcwd() + "/%s.png" % (item.name + '-' + str(uuid.uuid1())))


@pytest.fixture(scope="class")
def testenv(request):
    """Creates and yeild revizor TestEnv container.
       Destroys container after all tests in TestClass were executed,
       unless some of the tests failed.
    """
    container = TestEnv.create(branch='master')
    for _ in range(5):
        try:
            services = container.get_service_status()
            if all(service['state'] == 'RUNNING' for service in services):
                break
            time.sleep(3)
        except NoValidConnectionsError:
            time.sleep(3)
    ssh = container.get_ssh()
    ssh.run("rm -f /opt/scalr-server/libexec/mail/ssmtp")
    ssmtp_script = resources('scripts/ssmtp')
    container.put_file(
        ssmtp_script.fp.name,
        '/opt/scalr-server/libexec/mail/ssmtp')
    ssh.run('chmod 777 /opt/scalr-server/libexec/mail/ssmtp')
    yield container
    if request.node.session.testsfailed == 0:
        container.destroy()
