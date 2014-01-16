import os
import re
import time
import socket
import urllib2
import httplib
import logging
import traceback
from datetime import datetime

import requests
from lettuce import world

from revizor2.api import Farm, Role, IMPL
from revizor2.fixtures import resources
from revizor2.conf import CONF, roles_table
from revizor2.consts import ServerStatus, Platform, MessageStatus, BEHAVIORS_ALIASES
from revizor2.exceptions import NotFound
from revizor2.helpers.roles import get_role_versions


LOG = logging.getLogger(__name__)


@world.absorb
def give_empty_running_farm():
    farm_id = os.environ.get('RV_FARM_ID', CONF.main.farm_id)
    world.farm = Farm.get(farm_id)
    world.farm.roles.reload()
    if len(world.farm.roles):
        IMPL.farm.clear_roles(world.farm.id)
    world.farm.vhosts.reload()
    world.farm.domains.reload()
    for vhost in world.farm.vhosts:
        LOG.info('Delete vhost: %s' % vhost.name)
        vhost.delete()
    for domain in world.farm.domains:
        LOG.info('Delete domain: %s' % domain.name)
        domain.delete()
    if world.farm.terminated:
        world.farm.launch()
    LOG.info('Return empty running farm: %s' % world.farm.id)


@world.absorb
def add_role_to_farm(behavior, options=None, scripting=None, storages=None, alias=None):
    """
    Insert role to farm by behavior and find role in Scalr by generated name.
    Role name generate by the following format:
    {behavior}{RV_ROLE_VERSION}-{RV_DIST}-{RV_ROLE_TYPE}
    Moreover if we setup environment variable RV_ROLE_ID it added role with this ID (not by name)
    """
    if behavior in BEHAVIORS_ALIASES:
        behavior = BEHAVIORS_ALIASES[behavior]
    if CONF.feature.role_id:
        role = IMPL.role.get(CONF.feature.role_id)
        if not role:
            raise NotFound('Role with id %s not found in Scalr, please check' % CONF.feature.role_id)
    else:
        if CONF.feature.role_type == 'shared':
            #TODO: insert code to find shared role
            pass
        else:
            if CONF.feature.role_version:
                role_name = '%s%s-%s-%s' % (behavior, CONF.feature.role_version,
                                            CONF.feature.dist, CONF.feature.role_type)
            else:
                mask = '%s*-%s-%s' % (behavior, CONF.feature.dist, CONF.feature.role_type)
                versions = get_role_versions(mask)
                role_name = '%s%s-%s-%s' % (behavior, versions[0],
                                            CONF.feature.dist, CONF.feature.role_type)
            roles = IMPL.role.list(query=role_name)
            if not roles:
                raise NotFound('Role with name: %s not found in Scalr' % role_name)
            role = roles[0]
    old_roles_id = [r.id for r in world.farm.roles]
    world.farm.add_role(role['id'], options=options, scripting=scripting, storages=storages, alias=alias)
    time.sleep(3)
    world.farm.roles.reload()
    new_role = [r for r in world.farm.roles if r.id not in old_roles_id]
    if not new_role:
        raise AssertionError('Added role "%s" not found in farm' % role.name)
    return new_role[0]