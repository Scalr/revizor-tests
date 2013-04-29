import os
from datetime import datetime

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.api import Farm
from revizor2.consts import ServerStatus
from revizor2.utils import wait_until


@step('I add role to farm')
def add_role_to_given_farm(step):
    world.role_type = os.environ.get('RV_BEHAVIOR', 'base')
    role = world.add_role_to_farm(world.role_type)
    setattr(world, world.role_type + '_role', role)


@step('I have running server')
def having_a_running_server(step):
    world.farm = Farm.get(CONF.main.farm_id)
    world.server = None
    for server in world.farm.servers:
        if server.status == ServerStatus.RUNNING:
            world.server = server
            break
    world.assert_not_exist(world.server, 'Not see running server')


@step('I create server snapshot')
def rebundle(step):
    name = 'tmp-' + world.server.role.name + datetime.now().strftime('-%m%d-%H%M')
    bundle_id = world.server.create_snapshot('no_replace', name)
    if bundle_id:
        world.bundle_id = bundle_id


@step('Bundle task created')
def assert_bundletask_created(step):
    world.bundle_task_created(world.server, world.bundle_id)


@step('Bundle task becomes completed')
def assert_bundletask_completed(step, timeout=2400):
    wait_until(world.bundle_task_completed, args=(world.server, world.bundle_id), timeout=timeout, error_text="Bundle not completed")


@step('I add to farm role created by last bundle task')
def add_new_role_to_farm(step):
    world.farm.add_role(world.new_role_id)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, world.role_type + '_role', role)
