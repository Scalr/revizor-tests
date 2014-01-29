__author__ = 'gigimon'
import os
import time
import logging
from datetime import datetime

from lettuce import world, step

from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.consts import Platform


LOG = logging.getLogger(__name__)


@step('I change branch( to system)? for(?: (\w+))? role')
def change_branch_in_role_for_system(step, branch, role_type):
    """Change branch for selected role"""
    if 'system' in branch:
        branch = CONF.feature.branch
    else:
        branch = CONF.feature.to_branch
    LOG.info('Change branch to system for %s role' % role_type)
    role = world.get_role(role_type)
    role.edit(options={"user-data.scm_branch": branch})


@step('I increase minimum servers to (.+) for (.+) role')
def increase_instances(step, count, role_type):
    """Increase minimum servers count for role"""
    role = world.get_role(role_type)
    options = {"scaling.max_instances": int(count) + 1,
               "scaling.min_instances": count}
    world.farm.edit_role(role.role_id, options)


@step('I start a new server for(?: ([\w\d+]))? role')
def start_new_instance(step, role_type):
    role = world.get_role(role_type)
    LOG.info('Start new instance for role %s' % role)
    role.launch_instance()


@step('I create server snapshot for ([\w]+)$')
def rebundle_server(step, serv_as):
    """Start rebundle for server"""
    serv = getattr(world, serv_as)
    name = 'tmp-%s-%s' % (serv.role.name, datetime.now().strftime('%m%d%H%M'))
    bundle_id = serv.create_snapshot('no_replace', name)
    if bundle_id:
        world.bundle_id = bundle_id


@step('Bundle task created for ([\w]+)')
def assert_bundletask_created(step, serv_as):
    """Check bundle task status"""
    serv = getattr(world, serv_as)
    world.bundle_task_created(serv, world.bundle_id)


@step('Bundle task becomes completed for ([\w]+)')
def assert_bundletask_completed(step, serv_as, timeout=1800):
    serv = getattr(world, serv_as)
    wait_until(world.bundle_task_completed, args=(serv, world.bundle_id), timeout=timeout, error_text="Bundle not completed")


@step('I add to farm role created by last bundle task(?: as ([\w\d]+) role)?')
def add_new_role_to_farm(step, alias=None):
    options = getattr(world, 'role_options', {})
    scripting = getattr(world, 'role_scripting', [])
    bundled_role = Role.get(world.bundled_role_id)
    if 'redis' in bundled_role.behaviors:
        options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                        'db.msr.redis.use_password': True})
    world.farm.add_role(world.bundled_role_id, options=options, scripting=scripting, alias=alias)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, '%s_role' % role.alias, role)