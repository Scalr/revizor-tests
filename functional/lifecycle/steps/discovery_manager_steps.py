# coding: utf-8
"""
Created on 27.10.16
@author: Eugeny Kurkovich
"""
import time
import logging

from lettuce import world, step
from revizor2.conf import CONF
from revizor2.api import IMPL
from revizor2.exceptions import TimeoutError


LOG = logging.getLogger(__name__)

@step(r'I get an image from the server running in the cloud')
def get_node_image(step):
    node = getattr(world, 'cloud_server')
    if CONF.feature.driver.is_platform_gce:
        image = node.driver.ex_get_image(node.extra['image'])
    elif CONF.feature.driver.is_platform_ec2:
        image = node.driver.get_image(node.extra['image_id'])
    LOG.debug('Obtained image (%s - %s) from cloud instance %s' %(image.name, image.id, node.id))
    setattr(world, 'image', image)


@step(r'I run the server imports running in the cloud')
def launch_import_server(step):
    node = getattr(world, 'cloud_server')
    role = getattr(world, 'role')
    farm_role = getattr(world, '%s_role' % role['name'])
    LOG.info('Import to Scalr instance: %s' % node.id)
    import_res = IMPL.discovery_manager.import_server(
        farm_role_id=farm_role.id,
        platform=CONF.feature.driver.scalr_cloud,
        instance_id=node.id
    )
    assert import_res['success']
    setattr(world, 'cloud_server', None)


@step(r'I trigger the deploy and run scalr agent on the ([\w\d]+) server')
def deploy_agent(step, serv_as):
    server = getattr(world, serv_as)
    deploy_cmd = IMPL.discovery_manager.triggering_agent_deployment(server.id)['deploy_cmd']
    node = world.cloud.get_node(server)
    LOG.info('Run scalarizr: [%s] on the imported server: %s' % (deploy_cmd, server.id))
    assert not bool(node.run(deploy_cmd)[2])


@step(r'connection with agent on the ([\w\d]+) server was established')
def handle_agent_status(step, serv_as):
    server = getattr(world, serv_as)
    agent_status = dict()
    timeout = 300
    time_until = time.time() + timeout
    while time.time() <= time_until:
        action = agent_status.get('next_act', 'check-in')
        if action == 'ready':
            break
        LOG.info('Check "%s" action status' % action)
        agent_status = IMPL.discovery_manager.get_deployment_action_status(
            act=action,
            server_id=server.id)
        LOG.info('Action {} status: "{status}", next action: "{next_act}"'.format(action, **agent_status))
        time.sleep(5)
    else:
        msg = 'Timeout: %d seconds reached' % (timeout,)
        raise TimeoutError(msg, timeout)
