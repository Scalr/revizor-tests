# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import sys
import time
import json

import pytest
import requests
from paramiko import ssh_exception

from revizor2.helpers import logutil
from revizor2.testenv import TestEnv
from revizor2.backend import IMPL
from revizor2.conf import CONF
from api.utils.helpers import ColorPrint

TE_HOST_TPL = "{}.test-env.scalr.com"


pytest_plugins = [
    "api.plugins.app_session"
]


def download_specs(working_dir, te_id):
    specs = ['user.v1beta0.yml', 'account.v1beta0.yml', 'global.v1beta0.yml', 'openapi.v1beta0.yml']

    spec_dir = working_dir / 'specs'
    if not spec_dir.is_dir():
        spec_dir.mkdir()

    for spec in specs:
        spec_path = spec_dir / f'{spec}'
        if spec_path.is_file():
            continue
        ColorPrint.print_info(f'Download spec {spec} to file {spec_path}')
        resp = requests.get(f'http://{te_id}.test-env.scalr.com/api/{spec}')
        if resp.status_code != 200:
            continue
        with open(spec_path, 'w+') as fp:
            fp.write(resp.text)


def pytest_addoption(parser):
    group = parser.getgroup("revizor api testing", after="general")
    group.addoption(
        "--no-validate", dest="api_validation", action="store_false",
        help="Set default behavior of validation util, if 'False' api response not validate by flex"
    )
    group.addoption(
        "--te-id", "--test-environment-id", dest="te_id",
        action="store", help="Scalr test environment id to use existing env", default=None
    )
    group.addoption(
        "--te-br", "--test-environment-branch", dest="te_branch",
        action="store", help="Scalr branch", default="master"
    )
    group.addoption(
        "--te-notes", dest="te_notes", action="store",
        help="Scalr test environment description", default='api testing environment'
    )
    group.addoption(
        "--te-creation-timeout", "--te-ct", dest="te_timeout", action="store",
        help="Scalr test environment creation timeout", default=300, type=int
    )
    group.addoption(
        "--te-no-delete", dest="te_no_delete", action="store_true", default=False,
        help="Don't remove test environment after tests is finished"
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
    time_delta = time.time() + session.config.getoption("te_timeout")
    while time.time() <= time_delta:
        try:
            test_env.get_ssh()
            session.config.test_env = test_env
            break
        except (ssh_exception.NoValidConnectionsError, ssh_exception.SSHException):
            time.sleep(1)
    else:
        test_env.destroy()
        ColorPrint.print_fail("")
        raise RuntimeError("Test environment timeout expired...")
    # Create api v2 keys
    CONF.scalr.te_id = test_env.te_id

    working_dir = CONF.main.home / 'testenvs' / CONF.scalr.te_id
    config_file = working_dir / 'settings.json'
    te_config = {}

    if not working_dir.exists():
        working_dir.mkdir(parents=True)
    else:
        if config_file.is_file():
            with open(config_file, 'r') as f:
                te_config = json.load(f)
    if 'account_api' not in te_config:
        user_api_key = IMPL.api_key.new()
        te_config['account_api'] = {
            'id': user_api_key['keyId'],
            'secret': user_api_key['secretKey']
        }
    if 'global_api' not in te_config:
        global_api_key = IMPL.api_key.new(session='super_admin')
        te_config['global_api'] = {
            'id': global_api_key['keyId'],
            'secret': global_api_key['secretKey']
        }
    with open(config_file, 'w') as f:
        json.dump(te_config, f)
    # Store settings
    session.config.working_dir = working_dir
    session.config.api_environment = dict(
        host=TE_HOST_TPL.format(test_env.te_id),
        config=te_config
    )

    download_specs(working_dir, test_env.te_id)

    ColorPrint.print_pass("Test will run in this test environment: %s" % TE_HOST_TPL.format(test_env.te_id))


def pytest_sessionfinish(session):
    test_env = getattr(session.config, "test_env", None)
    no_delete = session.config.getoption('te_no_delete', default=False)
    if test_env and not no_delete:
        ColorPrint.print_fail("Destroy environment: %s ..." % test_env.te_id)
        test_env.destroy()


