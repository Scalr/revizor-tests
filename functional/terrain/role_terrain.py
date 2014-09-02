__author__ = 'gigimon'
import os
import time
import logging
from datetime import datetime

from lettuce import world, step

from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.consts import Platform, ServerStatus


LOG = logging.getLogger(__name__)


@step('I change branch(?: to (.+))? for(?: (\w+))? role')
def change_branch_in_role_for_system(step, branch, role_type):
    """Change branch for selected role"""
    if 'system' in branch:
        branch = CONF.feature.branch
    elif not branch.strip():
        branch = CONF.feature.to_branch
    else:
        branch = branch.strip()
    LOG.info('Change branch to system for %s role' % role_type)
    role = world.get_role(role_type)
    role.edit(options={"user-data.scm_branch": branch})


@step('I increase minimum servers to (.+) for (.+) role')
def increase_instances(step, count, role_type):
    """Increase minimum servers count for role"""
    role = world.get_role(role_type)
    options = {"scaling.max_instances": int(count) + 1,
               "scaling.min_instances": count}
    role.edit(options)


@step('I start a new server for(?: ([\w\d+]))? role')
def start_new_instance(step, role_type):
    role = world.get_role(role_type)
    LOG.info('Start new instance for role %s' % role)
    role.launch_instance()


@step(r'bootstrap (\d+) servers as \(([\w\d, ]+)\)(?: in (\w+) role)?$')
def bootstrap_many_servers(step, serv_count, serv_names, role_type, timeout=1400):
    serv_names = [s.strip() for s in serv_names.split(',')]
    role = world.get_role(role_type)
    options = {"scaling.max_instances": int(serv_count) + 1,
               "scaling.min_instances": int(serv_count)}
    role.edit(options)
    for i in range(int(serv_count)):
        LOG.info('Launch %s server' % (i+1))
        server = world.wait_server_bootstrapping(role, ServerStatus.RUNNING, timeout=timeout)
        LOG.info('Server %s bootstrapping as %s' % (server.id, serv_names[i]))
        setattr(world, serv_names[i], server)


@step('Bundle task created for ([\w]+)')
def assert_bundletask_created(step, serv_as):
    """Check bundle task status"""
    server = getattr(world, serv_as)
    world.bundle_task_created(server, world.bundle_id)


@step('Bundle task becomes completed for ([\w]+)')
def assert_bundletask_completed(step, serv_as, timeout=1800):
    server = getattr(world, serv_as)
    wait_until(world.bundle_task_completed, args=(server, world.bundle_id), timeout=timeout, error_text="Bundle not completed")


@step('I add to farm role created by last bundle task(?: as ([\w\d]+) role)?')
def add_new_role_to_farm(step, alias=None):
    LOG.info('Add rebundled role to farm with alias: %s' % alias)
    options = getattr(world, 'role_options', {})
    scripting = getattr(world, 'role_scripting', [])
    bundled_role = Role.get(world.bundled_role_id)
    alias = alias or bundled_role.name
    if 'redis' in bundled_role.behaviors:
        options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                        'db.msr.redis.use_password': True})
    world.farm.add_role(world.bundled_role_id, options=options, scripting=scripting, alias=alias)
    world.farm.roles.reload()
    role = world.get_role(alias)
    LOG.debug('Save Role object after insert rebundled role to farm as: %s/%s' % (role.id, alias))
    setattr(world, '%s_role' % alias, role)


@step('I change suspend policy in role to (\w+)')
def change_suspend_policy(step, policy):
    role = world.get_role()
    LOG.info('Change suspend policy for role %s to %s' % (role.alias, policy))
    role.edit(options={"base.resume_strategy": policy})