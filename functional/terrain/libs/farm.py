import os
import re
import time
import logging
from datetime import datetime

from lettuce import world

from defaults import Defaults
from revizor2.api import Farm, IMPL
from revizor2.conf import CONF
from revizor2.consts import BEHAVIORS_ALIASES, DATABASE_BEHAVIORS
from revizor2.exceptions import NotFound
from revizor2.helpers import farmrole
from revizor2.helpers.roles import get_role_versions

from lxml import etree

LOG = logging.getLogger(__name__)


@world.absorb
def give_empty_farm(launched=False):
    if CONF.main.farm_id is None:
        LOG.info('Farm ID not setted, create a new farm for test')
        world.farm = Farm.create('tmprev-%s' % datetime.now().strftime('%d%m%H%M%f'),
                                 "Revizor farm for tests\n"
                                 "RV_BRANCH={}\n"
                                 "RV_PLATFORM={}\n"
                                 "RV_DIST={}\n".format(
                                     CONF.feature.branch,
                                     CONF.feature.platform.name,
                                     CONF.feature.dist.dist
                                 ))
        CONF.main.farm_id = world.farm.id
    else:
        LOG.info('Farm ID is setted in config use it: %s' % CONF.main.farm_id)
        world.farm = Farm.get(CONF.main.farm_id)
    world.farm.roles.reload()
    if len(world.farm.roles):
        LOG.info('Clear farm roles')
        IMPL.farm.clear_roles(world.farm.id)
    world.farm.vhosts.reload()
    for vhost in world.farm.vhosts:
        LOG.info('Delete vhost: %s' % vhost.name)
        vhost.delete()
    try:
        world.farm.domains.reload()
        for domain in world.farm.domains:
            LOG.info('Delete domain: %s' % domain.name)
            domain.delete()
    except Exception:
        pass
    if world.farm.terminated and launched:
        world.farm.launch()
    elif world.farm.running and not launched:
        world.farm.terminate()
    LOG.info('Return empty running farm: %s' % world.farm.id)


@world.absorb
def add_role_to_farm(behavior, role_params, role_id=None):
    """
    Insert role to farm by behavior and find role in Scalr by generated name.
    Role name generate by the following format:
    {behavior}{RV_ROLE_VERSION}-{RV_DIST}-{RV_ROLE_TYPE}
    Moreover if we setup environment variable RV_ROLE_ID it added role with this ID (not by name)
    """
    env_role_id = CONF.feature.role_id
    if env_role_id and env_role_id.isdigit():
        LOG.info("Get role by env id: '%s'" % env_role_id)
        role = IMPL.role.get(env_role_id)
    elif env_role_id or not role_id:
        role = get_role_by_mask(behavior, env_role_id)
    else:
        role = IMPL.role.get(role_id)
    if not role:
        raise NotFound('Role with id %s not found in Scalr' % (env_role_id or role_id))

    world.wrt(etree.Element('meta', name='role', value=role['name']))
    world.wrt(etree.Element('meta', name='dist', value=role['dist']))
    previously_added_roles = [r.id for r in world.farm.roles]

    alias = role_params.alias or role['name']
    LOG.info('Add role %s with alias %s to farm' % (role['id'], alias))

    role_params = setup_farmrole_params(role_params, alias=alias, behavior=behavior)
    world.farm.add_role(role['id'], options=role_params.to_json())
    time.sleep(3)
    world.farm.roles.reload()

    added_role = [r for r in world.farm.roles if r.id not in previously_added_roles]
    if added_role:
        setattr(world, 'role_params_%s' % added_role[0].id, role_params)
        return added_role[0]
    raise AssertionError('Added role "%s" not found in farm' % role['name'])


@world.absorb
def get_farm_state(state):
    world.farm = Farm.get(world.farm.id)
    if world.farm.status == state:
        return True
    else:
        raise AssertionError('Farm is Not in %s state' % state)


@world.absorb
def setup_farmrole_params(role_params=None, alias=None, behavior=None):
    platform = CONF.feature.platform
    dist = CONF.feature.dist

    role_params = role_params or farmrole.FarmRoleParams(platform, alias=alias)
    Defaults.set_hostname(role_params)

    if dist.is_windows:
        role_params.advanced.reboot_after_hostinit = True
        if dist.mask in ('windows-2008', 'windows-2012') and platform.is_azure:
            LOG.debug('Dist is windows, set instance type')
            role_params.instance_type = 'Standard_A1'
    elif dist.id == 'scientific-6-x' or \
            (dist.id in ['centos-6-x', 'centos-7-x'] and platform.is_ec2):
        role_params.advanced.disable_iptables_mgmt = False

    if platform.is_ec2:
        role_params.global_variables.variables.append(
            role_params.global_variables,
            farmrole.Variable(
                name='REVIZOR_TEST_ID',
                value=getattr(world, 'test_id')
            )
        )
    if behavior == 'rabbitmq':
        role_params.network.hostname_template = ''
    elif behavior in DATABASE_BEHAVIORS:
        Defaults.set_db_storage(role_params)
        if behavior == 'redis':
            LOG.info('Insert redis settings')
            snapshotting_type = os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof')
            role_params.database.redis_persistence_type = snapshotting_type
            role_params.database.redis_use_password = True


def get_role_by_mask(behavior, mask=None):
    behavior = BEHAVIORS_ALIASES.get(behavior, None) or behavior
    if not mask:
        use_cloudinit_role = re.search(
            pattern="(-cloudinit)$",
            string=behavior)
        role_type = CONF.feature.role_type
        dist = CONF.feature.dist

        if use_cloudinit_role:
            dist_mask = dist.id
            ver_mask_tpl = 'tmp-{beh}-{dist}-*-*'
            role_name_tpl = 'tmp-{beh}-{dist}-{ver}'
        else:
            dist_mask = dist.mask
            ver_mask_tpl = '{beh}*-{dist}-{type}'
            role_name_tpl = '{beh}{ver}-{dist}-{type}'

        ver_mask_tpl_params = dict(
            beh=behavior,
            dist=dist_mask,
            type=role_type
        )
        mask = ver_mask_tpl.format(**ver_mask_tpl_params)
        LOG.info('Get role versions by mask: %s' % mask)

        role_version = get_role_versions(mask, use_latest=True)
        role_tpl_params = dict(
            beh=behavior,
            dist=dist_mask,
            ver=role_version,
            type=role_type
        )
        role_name = role_name_tpl.format(**role_tpl_params)
    else:
        role_name = mask
    LOG.info('Get role by name: %s' % role_name)
    roles = IMPL.role.list(query=role_name)
    if roles:
        return roles[0]
    if mask:
        get_role_by_mask(behavior)
    raise NotFound('Role with name: %s not found in Scalr' % role_name)
