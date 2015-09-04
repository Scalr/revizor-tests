# coding: utf-8

"""
Created on 09.01.2015
@author: Eugeny Kurkovich
"""

import logging

from datetime import datetime
from lettuce import step, world
from revizor2.conf import CONF
from revizor2.api import IMPL, Server
from revizor2.consts import Platform, Dist
from revizor2.utils import wait_until
from revizor2.helpers import install_behaviors_on_node

LOG = logging.getLogger(__name__)

@step(r'I install scalarizr to the server')
def install_scalarizr(step):
    cloud_server = getattr(world, 'cloud_server')
    cookbooks = ['base', 'scalarizr']
    branch = CONF.feature.branch

    # Windows handler
    if Dist.is_windows_family(CONF.feature.dist):
        return

    # Linux handler
    LOG.info('Install scalarizr from branch: %s on node: %s ' % (branch, cloud_server.name))
    args = (cloud_server, cookbooks, CONF.feature.driver.scalr_cloud.lower())
    install_behaviors_on_node(*args, branch=branch)

@step(r'I create image')
def create_image(step):
    cloud = world.cloud
    cloud_server = getattr(world, 'cloud_server')

    image_name = 'tmp-base-{}-{:%d%m%Y-%H%M}'.format(
        CONF.feature.dist,
        datetime.now()
    )
    # Set credentials to image creation
    kwargs = dict(
        node=cloud_server,
        name=image_name,
    )
    if CONF.feature.driver.is_platform_ec2:
        kwargs.update({ 'reboot': False})

    image = cloud.create_template(**kwargs)
    assert getattr(image, 'id', False), 'An image from a node object %s was not created' % cloud_server.name
    LOG.info('An image: %s from a node object: %s was created' % (image.id, cloud_server.name))
    setattr(world, 'image', image)
    LOG.debug('Image atrs: %s' % dir(image))
    LOG.debug('Image Name: %s' % image.name)
    if CONF.feature.driver.is_platform_idcf:
        forwarded_port = world.forwarded_port
        ip = world.ip
        assert cloud.close_port(cloud_server, forwarded_port, ip=ip), "Can't delete a port forwarding rule."
    LOG.info('Port forwarding rule was successfully removed.')

    assert cloud_server.destroy(), "Can't destroy node: %s." % cloud_server.id
    LOG.info('Virtual machine %s was successfully destroyed.' % cloud_server.id)
    setattr(world, 'cloud_server', None)

@step(r'I add image to the new role')
def create_role(step):
    cloud_location = CONF.platforms[CONF.feature.platform]['location'] \
        if not CONF.feature.driver.is_platform_gce else ""
    image_kwargs = dict(
        platform = CONF.feature.driver.scalr_cloud,
        cloud_location =  cloud_location,
        image_id = world.image.id
    )
    name = world.image.name or \
        'tmp-base-{}-{:%d%m%Y-%H%m}'.format(
            CONF.feature.dist,
            datetime.now()
        )
    behaviors = ['bas','chef']
    # Checking an image
    LOG.debug('Checking an image {image_id}:{platform}({cloud_location})'.format(**image_kwargs))
    IMPL.image.check(**image_kwargs)
    # Register image to the Scalr
    LOG.debug('Register image %s to the Scalr' % name)
    image_kwargs.update(dict(software=behaviors, name=name))
    IMPL.image.create(**image_kwargs)
    # Create new role
    role_kwargs = dict(
        name =  name,
        behaviors = behaviors,
        images = [dict(
            platform = CONF.feature.driver.scalr_cloud,
            cloudLocation =  cloud_location,
            imageId = world.image.id)])
    LOG.debug('Create new role {name}. Role options: {behaviors} {images}'.format(**role_kwargs))
    role = IMPL.role.create(**role_kwargs)
    setattr(world, 'role', role['role'])

@step(r'I add created role to the farm')
def setup_farm(step):
    role = getattr(world, 'role')
    branch = CONF.feature.feature.to_branch


@step(r'I trigger scalarizr update by Scalr UI')
def update_scalarizr_by_scalr_ui(step):
    pass


@step(r'^([\w\-]+) version is valid in ([\w\d]+)$')
def assert_version(step, service, serv_as):
    pass


@step(r'I fork ([A-za-z0-9\/\-\_]+) branch to ([A-za-z0-9\/\-\_]+)$')
def fark_git_branch(step, branch_from, branch_to):
    pass