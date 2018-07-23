import uuid

import pytest


def pytest_runtest_makereport(item, call):
    """Saves screenshot when test fails and saves it in /ui directory.
    """
    if call.when == 'call' and call.excinfo:
        item.instance.driver.save_screenshot("/vagrant/ui/%s.png" % (item.name + '-' + str(uuid.uuid1())))
