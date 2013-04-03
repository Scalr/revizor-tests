import re
import time
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.api import IMPL
from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.fixtures import images
from revizor2.utils import get_scalr_dist_name

LOG = logging.getLogger('import2')


@step('I have a (.+) server running in cloud$')
def given_server_in_cloud(step, mbeh):
    n = getattr(world, 'cloud_server', None)
    if n:
        n.destroy()
    cloud = Cloud()
    LOG.info('Create node in cloud')
    if mbeh == 'mbeh1':
        image = images(CONF.main.platform).filter({'dist': get_scalr_dist_name(CONF.main.dist), 'behavior':'mysql2'}).first()
    elif mbeh == 'mbeh2':
        image = images(CONF.main.platform).filter({'dist': get_scalr_dist_name(CONF.main.dist), 'behavior':'www'}).first()
    LOG.debug('Use image: %s' % image)
    node = cloud.create_node(image=image.keys()[0], userdata='scm-branch=%s' % CONF.main.branch)
    setattr(world, 'cloud_server', node)


@step('I execute on it import command with changed server')
def execute_import(step):
    time.sleep(180)
    role_name = 'test-import-%s' % datetime.now().strftime('%m%d-%H%M')
    LOG.info('Start import')
    server_id = IMPL.import2_start(platform=CONF.main.platform,
                                  roleName=role_name)
    start_cmd = IMPL.import_check(server_id=server_id).replace('https://my.scalr.net/messaging', 'http://localhost/')
    LOG.info('Start import command in scalarizr: %s' % start_cmd)
    shell = world.cloud_server.get_interactive()
    shell.send(start_cmd+'\n')
    buf = ''
    start = datetime.now()
    while (datetime.now()-start).seconds < 120:
        if shell.recv_ready():
            received = shell.recv(512)
            LOG.info('Receive: %s' % received)
            buf += received
            if 'Sleep 60 seconds before next attempt' in buf:
                shell.close()
                LOG.debug('Find message hello sended')
                break
        else:
            time.sleep(5)
    else:
        raise AssertionError('Not find phrase \'Sleep 60 seconds before next attempt\'')


@step('scalarizr send Hello message$')
def give_hello(step):
    LOG.info('Get list messages')
    out = world.cloud_server.run('szradm list-messages | grep Hello')
    LOG.debug('List messages: %s' % out)
    id = out[0].splitlines()[0].split('|')[1].strip()
    LOG.info('Hello message id: %s' % id)
    setattr(world, 'message_id', id)


@step('Hello message contain behaviors: (.+)')
def check_behaviors(step, behaviors):
    behaviors = behaviors.split(',')
    LOG.info('Get message details')
    out = world.cloud_server.run('szradm message-details %s' % world.message_id)[0]
    beh = [b.strip() for b in re.findall(r'behaviour:\n(.+)dist:', out, re.DOTALL)[0].replace('-','').strip().splitlines()]
    LOG.info('Finded behaviours in message Hello: %s' % beh)
    for b in behaviors:
        if b.strip() not in beh:
            raise AssertionError('Not find %s in finded behaviors' % b)
