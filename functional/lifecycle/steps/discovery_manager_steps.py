# coding: utf-8
"""
Created on 27.10.16 
@author: Eugeny Kurkovich
"""
import logging

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

@step(r'I get an image from the server running in the cloud')
def get_node_image(step):
    node = getattr(world, 'cloud_server')
    if CONF.feature.driver.is_platform_gce:
        image = node.driver.ex_get_image(node.extra['selfLink'])
    elif CONF.feature.driver.is_platform_ec2:
        image = node.driver.get_image(node.extra['image_id'])
    LOG.debug('Obtained image (%s - %s) from cloud instance %s' %(image.name, image.id, node.id))
    setattr(world, 'image', image)


@step(r'I run the server imports running in the cloud')
def launch_import_server(step):
    import time
    time.sleep(300)
