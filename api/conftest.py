# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import sys
import time

import pytest

from paramiko import ssh_exception

from revizor2.testenv import TestEnv
from revizor2.backend import IMPL
from revizor2.conf import CONF


TE_HOST_TPL = "{}.test-env.scalr.com"
TE_URI_SCHEMA = "http"


def pytest_addoption(parser):
    parser.addoption(
        "--flex-validation", "--fv", dest="flex_validation", action="store_true", default=False,
        help="Set default behavior of validation util, if 'False' api response not validate by flex"
    )
    parser.addoption(
        "--te_id", "--test_environment_id", dest="te_id",
        action="store", help="Scalr test environment id", default=None
    )
    parser.addoption(
        "--te_br", "--test_environment_branch", dest="te_branch",
        action="store", help="Scalr branch", default="master"
    )
    parser.addoption(
        "--te_notes", dest="te_notes", action="store",
        help="Scalr test environment description", default='api testing environment'
    )
    parser.addoption(
        "--remove-test-env", dest="remove_te",
        action="store", help="Remove Scalr test environment after test is finished",
        default=True
    )
    parser.addoption(
        "--show-capture-repress", dest="no_show_capture",
        action="store", help="Repress capture output", default=True
    )


def pytest_sessionstart(session):
    te_id = session.config.getoption("te_id")
    if session.config.getoption('no_show_capture'):
        session.config.option.showcapture = 'no'
    if not te_id:
        sys.stdout.write("\033[0;32m\nPrepare Scalr environment...\n")
        test_env = TestEnv.create(
            branch=session.config.getoption("te_branch"),
            notes=session.config.getoption("te_notes"))
        # Wait test environment is Running
        while True:
            try:
                test_env.get_ssh()
                break
            except ssh_exception.NoValidConnectionsError:
                time.sleep(1)
        session.config.test_env = test_env
    else:
        test_env = TestEnv(te_id)
    # Create api v2 keys
    CONF.scalr.te_id = test_env.te_id
    api_key = IMPL.api_key.new()
    # Store settings
    session.config.api_environment = dict(
        host=TE_HOST_TPL.format(test_env.te_id),
        schema=TE_URI_SCHEMA,
        secret_key=api_key['secretKey'],
        secret_key_id=api_key['keyId']
    )
    sys.stdout.write(
        "\033[0;32m\n\nTest will run in this test environment: %s\n" %
        TE_HOST_TPL.format(test_env.te_id))


def pytest_sessionfinish(session):
    test_env = getattr(session.config, "test_env", None)
    if session.config.getoption('remove_te') and test_env:
        sys.stdout.write("\033[1;31m\n\nDestroy environment: %s ..." % test_env.te_id)
        test_env.destroy()


pytest_plugins = [
    "api.plugins.filefixture",
    "api.utils.app_session"
]
