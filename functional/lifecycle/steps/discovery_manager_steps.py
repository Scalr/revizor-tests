# coding: utf-8
"""
Created on 27.10.16
@author: Eugeny Kurkovich
"""
import time
import logging

from lettuce import world, step
from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.exceptions import TimeoutError


LOG = logging.getLogger(__name__)


@step(r'I get an image from the server running in the cloud')
def get_node_image(step):
    node = getattr(world, 'cloud_server')
    if node.platform_config.is_gce:
        image = node.driver.ex_get_image(node.extra['image'])
    elif node.platform_config.is_ec2:
        image = node.driver.get_image(node.extra['image_id'])
    elif node.platform_config.is_azure:
        image = node.cloud.find_image()
    LOG.debug('Obtained image (%s - %s) from cloud instance %s' % (image.name, image.id, node.id))
    setattr(world, 'image', image)


@step(r'I run the server imports running in the cloud')
def launch_import_server(step):
    node = getattr(world, 'cloud_server')
    role = getattr(world, 'role')
    farm_role = getattr(world, '%s_role' % role['name'])
    if CONF.feature.platform.is_azure:
        node_id = node.name
        res_group = 'revizor'
    else:
        node_id = node.id
        res_group = None
    LOG.info('Import to Scalr instance: %s' % node_id)
    import_res = IMPL.discovery_manager.import_server(
        farm_role_id=farm_role.id,
        platform=CONF.feature.platform.name,
        instance_id=node_id,
        resource_group=res_group
    )
    assert import_res['success']
    setattr(world, 'cloud_server', None)


@step(r'I trigger the deploy and run scalr agent on the ([\w\d]+) server')
def deploy_agent(step, serv_as):
    server = getattr(world, serv_as)
    deploy_cmd = IMPL.discovery_manager.triggering_agent_deployment(server.id)['deploy_cmd']
    node = world.cloud.get_node(server)
    LOG.info('Run scalarizr: [%s] on the imported server: %s' % (deploy_cmd, server.id))
    assert not bool(node.run(deploy_cmd).status_code)


@step(r'connection with agent on the ([\w\d]+) server was established')
def handle_agent_status(step, serv_as):
    server = getattr(world, serv_as)
    agent_status = dict()
    timeout = 300
    time_until = time.time() + timeout
    while time.time() <= time_until:
        LOG.info('Check agent deploy status')
        agent_status = IMPL.discovery_manager.get_deployment_action_status(
            act='check',
            server_id=server.id)
        LOG.info('Agent deploy status: %s' % agent_status)
        if agent_status.get('status') == 'ready':
            break
        time.sleep(5)
    else:
        msg = 'Timeout: %d seconds reached' % (timeout,)
        raise TimeoutError(msg, timeout)
