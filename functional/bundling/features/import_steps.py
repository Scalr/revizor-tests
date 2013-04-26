import os
import time
from datetime import datetime
import logging

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.api import Farm, IMPL, Server
from revizor2.consts import ServerStatus, OS, Platform
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.fixtures import tables


LOG = logging.getLogger('import')


@step('I have a server running in cloud$')
def given_server_in_cloud(step):
    #TODO: Add install behaviors
    LOG.info('Create node in cloud')
    node = world.cloud.create_node()
    LOG.info('Install scalarizr in node')
    node.install_scalarizr(branch=CONF.main.branch)
    setattr(world, 'cloud_server', node)
    #FIXME: delete this
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        new_port = world.cloud.open_port(node, 8013)
        if not new_port == 8013:
            raise AssertionError('Import will failed, because opened port is not 8013')


@step('I execute on it import command$')
def execute_import(step):
    time.sleep(180)
    role_name = 'test-import-%s' % datetime.now().strftime('%m%d-%H%M')
    LOG.info('Start import')
    server_id = IMPL.bundle.import_start(platform=CONF.main.platform, name=role_name)
    start_cmd = IMPL.bundle.import_check(server_id=server_id)
    LOG.info('Start import command in scalarizr: %s' % start_cmd)
    world.server = Server(**{'id':server_id})
    world.cloud_server.run('screen -d -m %s &' % start_cmd)


@step('Scalr receives ([\w\d]+)$')
def check_message(step, msgname, timeout=1400):
    msgname = msgname.strip()
    wait_until(world.check_message_status, args=(msgname, world.server, 'receives'), timeout=timeout, error_text="I'm not see this %s state in server" % msgname)


@step('bundle task was created$')
def assert_bundle_task_created(step):
    time.sleep(60)
    world.bundle_id = world.server.bundlelogs[0].id
    world.bundle_task_created(world.server, world.bundle_id)


@step('I add to farm imported role$')
def add_new_role_to_farm(step):
    world.farm.add_role(world.new_role_id)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, 'role_type', ','.join(role.role.behaviors))
    setattr(world, '%s_role' % ','.join(role.role.behaviors), role)
