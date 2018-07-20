import pytest
import time

from revizor2.testenv import TestEnv


@pytest.fixture(scope="class")
def testenv(request):
    container = TestEnv.create(branch='master')
    time.sleep(15)
    request.node.obj.container = container
    yield
    if request.node.session.testsfailed == 0:
        container.destroy()
