import os
import re
import logging
import types
from datetime import datetime

from lettuce import world

from defaults import Defaults
from revizor2.api import Farm, IMPL
from revizor2.conf import CONF
from revizor2.consts import BEHAVIORS_ALIASES, DATABASE_BEHAVIORS
from revizor2.exceptions import NotFound
from revizor2.helpers import farmrole
from revizor2.helpers.roles import get_role_versions

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
def get_farm_state(state):
    world.farm = Farm.get(world.farm.id)
    if world.farm.status == state:
        return True
    else:
        raise AssertionError('Farm is Not in %s state' % state)


@world.absorb
def setup_farmrole_params(
        role_options=None,
        alias=None,
        behaviors=None,
        setup_bundled_role=False):

    platform = CONF.feature.platform
    dist = CONF.feature.dist
    behaviors = behaviors or []
    role_options = role_options or []
    role_params = farmrole.FarmRoleParams(platform, alias=alias)

    if isinstance(behaviors, types.StringType):
        behaviors = [behaviors]

    if not (setup_bundled_role and len('{}-{}'.format(world.farm.name, alias)) < 63):
        Defaults.set_hostname(role_params)

    for opt in role_options:
        LOG.info('Inspect role option: %s' % opt)
        if opt in ('branch_latest', 'branch_stable'):
            role_params.advanced.agent_update_repository = opt.split('_')[1]
        elif 'redis processes' in opt:
            redis_count = re.findall(r'(\d+) redis processes', opt)[0].strip()
            LOG.info('Setup %s redis processes' % redis_count)
            role_params.database.redis_processes = int(redis_count)
        elif 'chef-solo' in opt:
            Defaults.set_chef_solo(role_params, opt)
        else:
            Defaults.apply_option(role_params, opt)

    if not setup_bundled_role:
        if dist.is_windows:
            role_params.advanced.reboot_after_hostinit = True
            if dist.mask in ('windows-2008', 'windows-2012') and platform.is_azure:
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
        if 'rabbitmq' in behaviors:
            role_params.network.hostname_template = ''

    if any(b in DATABASE_BEHAVIORS for b in behaviors):
        Defaults.set_db_storage(role_params)
        if 'redis' in behaviors:
            LOG.info('Insert redis settings')
            snapshotting_type = os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof')
            role_params.database.redis_persistence_type = snapshotting_type
            role_params.database.redis_use_password = True

    return role_params


@world.absorb
def get_role_by_mask(behavior, mask=None):
    behavior = BEHAVIORS_ALIASES.get(behavior, None) or behavior
    dist = CONF.feature.dist
    if not mask:
        use_cloudinit_role = "-cloudinit" in behavior
        role_type = CONF.feature.role_type

        if use_cloudinit_role:
            dist_mask = dist.id
            role_ver_tpl = 'tmp-{beh}-{dist}-*-*'
            role_name_tpl = 'tmp-{beh}-{dist}-{ver}'
        else:
            dist_mask = dist.mask
            role_ver_tpl = '{beh}*-{dist}-{type}'
            role_name_tpl = '{beh}{ver}-{dist}-{type}'

        role_ver_mask = role_ver_tpl.format(
            beh=behavior,
            dist=dist_mask,
            type=role_type)
        LOG.info('Get role versions by mask: %s' % role_ver_mask)

        role_version = get_role_versions(role_ver_mask, use_latest=True)
        role_name = role_name_tpl.format(
            beh=behavior,
            dist=dist_mask,
            ver=role_version,
            type=role_type)
    else:
        role_name = mask
    LOG.info('Get role by name: %s' % role_name)
    roles = IMPL.role.list(dist=dist.dist, query=role_name)
    if roles:
        return roles[0]
    if mask:
        get_role_by_mask(behavior)
    raise NotFound('Role with name: %s not found in Scalr' % role_name)
