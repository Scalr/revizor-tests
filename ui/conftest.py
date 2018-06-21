import uuid


def pytest_runtest_makereport(item, call):
    if call.when == 'call' and call.excinfo:
        item.instance.driver.save_screenshot("/vagrant/ui/%s.png" % (item.name + '-' + str(uuid.uuid1())))
