import time
from datetime import datetime
import logging

from threading import Thread

from lettuce import world, step, after
from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.api import IMPL, Server
from revizor2.consts import Platform, Dist
from revizor2.defaults import USE_VPC
from revizor2.utils import wait_until
from revizor2.helpers import install_behaviors_on_node
from revizor2.fixtures import tables

LOG = logging.getLogger(__name__)


@step('Role has successfully been created$')
def assert_role_task_created(step,  timeout=1400):
    res = wait_until(
        IMPL.bundle.assert_role_task_created,
        args=(world.bundle_task.get('id'), ),
        timeout=timeout,
        error_text="Time out error. Can't create role with behaviors: %s." % CONF.feature.behaviors)
    if res.get('failure_reason'):
        raise AssertionError("Can't create role: %s. Error: %s" % (res['role_id'],res['failure_reason']))
    LOG.info('New role was created successfully with Role_id: %s.' % res['role_id'])
    world.bundled_role_id = res['role_id']
    #Remove port forward rule for Cloudstack
    if CONF.feature.driver.current_cloud in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        LOG.info('Deleting a Port Forwarding Rule. IP:%s, Port:%s' % (world.forwarded_port, world.ip))
        if not world.cloud.close_port(world.cloud_server, world.forwarded_port, ip=world.ip):
            raise AssertionError("Can't delete a port forwarding Rule.")
        LOG.info('Port Forwarding Rule was successfully removed.')
    #Destroy virtual machine in Cloud
    LOG.info('Destroying virtual machine %s in Cloud' % world.cloud_server.id)
    try:
        if not world.cloud_server.destroy():
            raise AssertionError("Can't destroy node with id: %s." % world.cloud_server.id)
    except Exception as e:
        if CONF.feature.driver.current_cloud == Platform.GCE:
            if world.cloud_server.name in str(e):
                pass
        else:
            raise
    LOG.info('Virtual machine %s was successfully destroyed.' % world.cloud_server.id)
    world.cloud_server = None


@after.each_scenario
def cleanup_cloud_server(total):
    LOG.info('Cleanup cloud server after import')
    cloud_node = getattr(world, 'cloud_server', None)
    if cloud_node:
        LOG.info('Destroy node in cloud')
        try:
            cloud_node.destroy()
        except BaseException, e:
            LOG.exception('Node %s can\'t be destroyed' % cloud_node.id)


