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
from api.utils.helpers import ColorPrint


TE_HOST_TPL = "{}.test-env.scalr.com"


def pytest_addoption(parser):
    group = parser.getgroup("docker controller", "fatmouse", after="general")
    group.addoption(
        "--flex-validation", "--fv", dest="flex_validation", action="store_true", default=False,
        help="Set default behavior of validation util, if 'False' api response not validate by flex"
    )
    group.addoption(
        "--te-id", "--test-environment_id", dest="te_id",
        action="store", help="Scalr test environment id to use existing env", default=None
    )
    group.addoption(
        "--te-br", "--test-environment_branch", dest="te_branch",
        action="store", help="Scalr branch", default="master"
    )
    group.addoption(
        "--te-notes", dest="te_notes", action="store",
        help="Scalr test environment description", default='api testing environment'
    )
    group.addoption(
        "--te-creation-timeout", "--te-ct", dest="te_timeout", action="store",
        help="Scalr test environment creation timeout", default=60, type=int
    )
    group.addoption(
        "--store-test-env", dest="store_te", action="store_true",
        help="Store Scalr test environment after tests is finished"
    )


def pytest_sessionstart(session):
    if "--show-capture" not in sys.argv:
        session.config.option.showcapture = 'no'
    te_id = session.config.getoption("te_id")
    if not te_id:
        ColorPrint.print_pass("Prepare Scalr environment...")
        test_env = TestEnv.create(
            branch=session.config.getoption("te_branch"),
            notes=session.config.getoption("te_notes"))
    else:
        test_env = TestEnv(te_id)
    # Wait test environment is Running
    time_delta = time.time()+session.config.getoption("te_timeout")
    while time.time() <= time_delta:
        try:
            test_env.get_ssh()
            session.config.test_env = test_env
            break
        except ssh_exception.NoValidConnectionsError:
            time.sleep(1)
    else:
        ColorPrint.print_fail("")
        raise RuntimeError("Test environment timeout expired...")
    # Create api v2 keys
    CONF.scalr.te_id = test_env.te_id
    api_key = IMPL.api_key.new()
    # Store settings
    session.config.api_environment = dict(
        host=TE_HOST_TPL.format(test_env.te_id),
        schema="http",
        secret_key=api_key['secretKey'],
        secret_key_id=api_key['keyId']
    )
    ColorPrint.print_pass("Test will run in this test environment: %s" % TE_HOST_TPL.format(test_env.te_id))


def pytest_sessionfinish(session):
    test_env = getattr(session.config, "test_env", None)
    store_test_env = session.config.getoption('store_te', default=False)
    if test_env and not store_test_env:
        ColorPrint.print_fail("Destroy environment: %s ..." % test_env.te_id)
        test_env.destroy()


pytest_plugins = [
    "api.plugins.filefixture",
    "api.utils.app_session"
]
