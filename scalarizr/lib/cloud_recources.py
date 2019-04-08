# coding: utf-8
"""
Created on 02.04.19
@author: Eugeny Kurkovich
"""

import logging

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.utils import wait_until

LOG = logging.getLogger(__name__)


def efs_create(name, location, vpc_id, user_id) -> dict:
    """ Creates an Amazon EC2 efs
    """
    efs = IMPL.aws_tools.efs_create(
        name=name,
        location=location,
        vpc_id=vpc_id,
        user_id=user_id
    )
    efs_details = IMPL.aws_tools.efs_details
    wait_until(
        lambda status: efs_details(
            efs['fileSystemId'],
            location)['status'] == status,
        ('available',),
        timeout=90,
        logger=LOG,
        error_text=f"An Amazon efs [{efs['fileSystemId']}] is not available"
    )
    return efs


def create_efs_mount_target(efs_id, vpc_id,
                            vpc_subnet_id, vpc_subnet_availability_zone,
                            location, wait_availability=False) -> str:
    """Create mount target for new efs
    """
    mount_target = IMPL.aws_tools.create_efs_mount_target(
        efs_id=efs_id,
        vpc_id=vpc_id,
        vpc_subnet_id=vpc_subnet_id,
        location=location,
        availability_zone=vpc_subnet_availability_zone
    )
    efs_details = IMPL.aws_tools.efs_details
    if wait_availability:
        wait_until(
            lambda status: efs_details(
                efs_id,
                location)['mountTargets'][0]['status'] == status,
            ('available',),
            timeout=180,
            logger=LOG,
            error_text=f"Mount target was not created properly for amazon efs [{efs_id}]"
        )
    return mount_target['mountTargetId']


def delete_efs(cloud_id, cloud_location, **kwargs):
    """Delete an Amazon efs and it mount targets
    """
    IMPL.aws_tools.delete_efs_mount_targets(cloud_id, cloud_location)
    wait_until(
        lambda: not IMPL.aws_tools.efs_details(
            cloud_id,
            cloud_location)['mountTargets'],
        timeout=90,
        logger=LOG,
        error_text=f"An Amazon efs [{cloud_id}] mount targets was not properly removed"
    )
    IMPL.aws_tools.efs_delete(cloud_id, cloud_location)
