__author__ = 'gigimon'
import os
import re
import time
import logging

from lettuce import world, step

from libs.defaults import Defaults
from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.consts import DATABASE_BEHAVIORS
from revizor2.helpers import farmrole
from revizor2.utils import wait_until


LOG = logging.getLogger(__name__)


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_farm(launched=True)


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
    """Clear all roles from farm and stop farm"""
    world.give_empty_farm(launched=False)


@step(r"I add(?P<behavior> \w+-?\w+?)? role(?P<saved_role> [\w\d]+)? to this farm(?: with (?P<options>(?:(?! as )[ \w\d,-])+))?(?: as (?P<alias>[\w\d]+))?")
def add_role_to_farm(step, behavior=None, saved_role=None, options=None, alias=None):
    role_id = None
    old_branch = CONF.feature.branch
    options = options or []

    if saved_role:
        role_id = getattr(world, '%s_id' % saved_role.strip())
    if not behavior:
        behavior = os.environ.get('RV_BEHAVIOR', 'base')
    else:
        behavior = behavior.strip()

    platform = CONF.feature.platform
    role_params = farmrole.FarmRoleParams(platform, alias=alias)
    Defaults.set_hostname(role_params)

    if options:
        for opt in [o.strip() for o in options.strip().split(',')]:
            LOG.info('Inspect option: %s' % opt)
            if opt in ('branch_latest', 'branch_stable'):
                CONF.feature.branch = opt.split('_')[1]
            elif 'redis processes' in opt:
                redis_count = re.findall(r'(\d+) redis processes', options)[0].strip()
                LOG.info('Setup %s redis processes' % redis_count)
                role_params.database.redis_processes = int(redis_count)
            elif 'chef-solo' in opt:
                Defaults.set_chef_solo(role_params, opt)
            else:
                Defaults.apply_option(role_params, opt)

    if CONF.feature.dist.id == 'scientific-6-x' or \
            (CONF.feature.dist.id in ['centos-6-x', 'centos-7-x'] and platform.is_ec2):
        role_params.advanced.disable_iptables_mgmt = False

    if CONF.feature.dist.is_windows:
        role_params.advanced.reboot_after_hostinit = True

    if behavior == 'rabbitmq':
        role_params.network.hostname_template = ''

    if behavior == 'redis':
        LOG.info('Insert redis settings')
        role_params.database.redis_persistence_type = os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof')
        role_params.database.redis_use_password = True

    if behavior in DATABASE_BEHAVIORS:
        Defaults.set_db_storage(role_params)

    role = world.add_role_to_farm(behavior, role_params, role_id)

    LOG.debug('Save role object with name %s' % role.alias)
    setattr(world, '%s_role' % role.alias, role)
    if 'branch_latest' in options or 'branch_stable' in options:
        CONF.feature.branch = old_branch


@step('I delete (\w+) role from this farm')
def delete_role_from_farm(step, role_type):
    LOG.info('Delete role %s from farm' % role_type)
    role = world.get_role(role_type)
    world.farm.delete_role(role.role_id)


@step('I (?:terminate|stop) farm')
def farm_terminate(step):
    """Terminate (stopping) farm"""
    world.farm.terminate()
    time.sleep(30)


@step('I start farm$')
def farm_launch(step):
    """Start farm"""
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I start farm with delay$')
def farm_launch(step):
    """Start farm with delay for cloudstack"""
    if CONF.feature.platform.is_cloudstack: #Maybe use on all cloudstack
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I add to farm imported role$')
def add_new_role_to_farm(step):
    bundled_role = Role.get(world.bundled_role_id)
    options = farmrole.FarmRoleParams(CONF.feature.platform, alias=bundled_role.name)
    world.farm.add_role(
        world.bundled_role_id,
        options=options.to_json())
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, '%s_role' % role.alias, role)


@step('I suspend farm')
def farm_state_suspend(step):
    """Suspend farm"""
    world.farm.suspend()


@step('I resume farm')
def farm_resume(step):
    """Resume farm"""
    world.farm.resume()


@step('I wait farm in ([\w]+) state')
def wait_for_farm_state(step, state):
    """Wait for state of farm"""
    wait_until(world.get_farm_state, args=(
        state, ), timeout=300, error_text=('Farm have no status %s' % state))
