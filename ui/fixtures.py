import pytest
import time

from revizor2.testenv import TestEnv


@pytest.fixture(scope="module")
def testenv():
    container = TestEnv.create(branch='master')
    time.sleep(15)
    return container
