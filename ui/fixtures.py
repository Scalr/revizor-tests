import time

import pytest
from paramiko.ssh_exception import NoValidConnectionsError

import os
from pathlib import Path

from revizor2.testenv import TestEnv


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
    local_path_to_ssmtp = '/vagrant/revizor/etc/fixtures/resources/scripts/ssmtp' if 'vagrant' in str(Path.home()) else None
    if not local_path_to_ssmtp:
        for root, dirs, files in os.walk(Path.home()):
            for name in files:
                if name == 'ssmtp':
                    local_path_to_ssmtp = os.path.abspath(
                        os.path.join(root, name))
                    break
    if not local_path_to_ssmtp:
        raise FileNotFoundError("Can't find ssmtp script. Check revizor folder.")
    container.put_file(
        local_path_to_ssmtp,
        '/opt/scalr-server/libexec/mail/ssmtp')
    ssh.run('chmod 777 /opt/scalr-server/libexec/mail/ssmtp')
    yield container
    if request.node.session.testsfailed == 0:
        container.destroy()
