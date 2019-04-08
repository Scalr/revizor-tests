# coding: utf-8
"""
Created on 02.04.19
@author: Eugeny Kurkovich
"""
import json
import pytest
import logging

from random import randint

from scalarizr.lib import scalr
from scalarizr.lib import cloud_recources as lib_recources
from revizor2.conf import CONF
from revizor2.backend import IMPL


LOG = logging.getLogger(__name__)


@pytest.fixture
def efs() -> dict:
    platform = CONF.feature.platform
    user = scalr.get_scalr_user_by_email_local_part("test")
    # New efs
    LOG.info('Create new Amazon elastic file system')
    efs = lib_recources.efs_create(
        f"revizor-{randint(9000, 9999)}",
        platform.location,
        platform.vpc_id,
        user[0]['id']
    )
    # Add mount target to efs
    mount_target = lib_recources.create_efs_mount_target(
        efs['fileSystemId'],
        platform.vpc_id,
        json.loads(platform.vpc_subnet_id)[0],
        platform.zone,
        platform.location)
    LOG.debug(f'Added new EFS [{efs["fileSystemId"]}] with mounts target [{mount_target}].')
    return efs
