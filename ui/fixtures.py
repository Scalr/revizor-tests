import time

import pytest
from paramiko.ssh_exception import NoValidConnectionsError

from revizor2.testenv import TestEnv
from pages import LoginPage


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
    yield container
    if request.node.session.testsfailed == 0:
        container.destroy()
