# coding: utf-8

"""
Created on 09.01.2015
@author: Eugeny Kurkovich
"""

import re
import logging

from datetime import datetime
from revizor2.api import IMPL
from revizor2.conf import CONF
from lettuce import step, world, after
from revizor2.consts import Dist
from revizor2.defaults import USE_VPC
from distutils.version import LooseVersion
from revizor2.utils import wait_until


LOG = logging.getLogger(__name__)

def get_user_name():
    if CONF.feature.driver.is_platform_gce:
        user_name = 'scalr'
    elif 'ubuntu' in CONF.feature.dist:
        user_name = ['ubuntu', 'root']
    elif 'amzn' in CONF.feature.dist:
        user_name = 'ec2-user'
    else:
        user_name = 'root'
    return user_name


@step(r'I have a clean image')
def having_clean_image(step):
    cloud = world.cloud
    image = cloud.find_image(use_hvm=USE_VPC)
    LOG.debug('Obtained clean image %s, Id: %s' %(image.name, image.id))
    setattr(world, 'image', image)


@step(r'I install scalarizr to the server(?: (\w+))?')
def installing_scalarizr(step, serv_as=''):
    node =  getattr(world, 'cloud_server', None)
    branch = CONF.feature.branch
    repo = CONF.feature.ci_repo.lower()
    platform = CONF.feature.driver.scalr_cloud()
    # Wait cloud server
    if not node:
        LOG.debug('Cloud server not found get node from server')
        server = getattr(world, serv_as.strip())
        server.reload()
        node = wait_until(world.cloud.get_node, args=(server, ), timeout=300, logger=LOG)
        LOG.debug('Node get successfully: %s' % node)
    assert node,  'Node not found'
    # Windows handler
    if Dist.is_windows_family(CONF.feature.dist):
        return
    # Linux handler
    else:
        # Wait ssh
        ssh = wait_until(node.get_ssh, kwargs=dict(user=get_user_name()), timeout=300, logger=LOG)
        LOG.info('Installing scalarizr from branch: %s to node: %s ' % (branch, node.name))
        cmd = '{curl_install} && ' \
            'PLATFORM={platform} ; ' \
            'CI_REPO={repo} ; ' \
            'BRANCH={branch} ; ' \
            'curl -L http://my.scalr.net/public/linux/$CI_REPO/$PLATFORM/$BRANCH/install_scalarizr.sh | bash &&' \
            'scalarizr -v'.format(
                curl_install=world.value_for_os_family(
                    debian="apt-get update && apt-get install curl -y",
                    centos="yum clean all && yum install curl -y",
                    server=server),
                platform=platform,
                repo=repo,
                branch=branch)
        res = node.run(cmd, ssh=ssh)[0].splitlines()[-1].strip()
    version = re.findall('(Scalarizr [a-z0-9/./-]+)', res)
    assert  version, 'Could not install scalarizr'
    setattr(world, 'pre_installed_agent', version[0].split()[1])
    LOG.debug('Scalarizr %s was successfully installed' % world.pre_installed_agent)


@step(r'I create image from deployed server')
def creating_image(step):
    cloud_server = getattr(world, 'cloud_server')
    # Create an image
    image_name = 'tmp-base-{}-{:%d%m%Y-%H%M%S}'.format(
        CONF.feature.dist,
        datetime.now()
    )
    # Set credentials to image creation
    kwargs = dict(
        node=cloud_server,
        name=image_name,
    )
    if CONF.feature.driver.is_platform_ec2:
        kwargs.update({'reboot': False})
    image = world.cloud.create_template(**kwargs)
    assert getattr(image, 'id', False), 'An image from a node object %s was not created' % cloud_server.name
    # Remove cloud server
    LOG.info('An image: %s from a node object: %s was created' % (image.id, cloud_server.name))
    setattr(world, 'image', image)
    LOG.debug('Image attrs: %s' % dir(image))
    LOG.debug('Image Name: %s' % image.name)
    if CONF.feature.driver.is_platform_cloudstack:
        forwarded_port = world.forwarded_port
        ip = world.ip
        assert world.cloud.close_port(cloud_server, forwarded_port, ip=ip), "Can't delete a port forwarding rule."
    LOG.info('Port forwarding rule was successfully removed.')
    assert cloud_server.destroy(), "Can't destroy node: %s." % cloud_server.id
    LOG.info('Virtual machine %s was successfully destroyed.' % cloud_server.id)
    setattr(world, 'cloud_server', None)


@step(r'I add image to the new role')
def creating_role(step):
    image_registered = False
    cloud_location = CONF.platforms[CONF.feature.platform]['location'] \
        if not CONF.feature.driver.is_platform_gce else ""
    image_kwargs = dict(
        platform=CONF.feature.driver.scalr_cloud,
        cloud_location=cloud_location,
        image_id=world.image.id
    )
    name = 'tmp-base-{}-{:%d%m%Y-%H%M%S}'.format(
            CONF.feature.dist,
            datetime.now())
    behaviors = ['chef']
    # Checking an image
    try:
        LOG.debug('Checking an image {image_id}:{platform}({cloud_location})'.format(**image_kwargs))
        IMPL.image.check(**image_kwargs)
    except Exception as e:
        if not ('Image has already been registered' in e.message):
            raise
        image_registered = True
    if not image_registered:
        # Register image to the Scalr
        LOG.debug('Register image %s to the Scalr' % name)
        image_kwargs.update(dict(software=behaviors, name=name))
        IMPL.image.create(**image_kwargs)
    # Create new role
    role_kwargs = dict(
        name=name,
        behaviors=behaviors,
        images=[dict(
            platform=CONF.feature.driver.scalr_cloud,
            cloudLocation=cloud_location,
            imageId=world.image.id)])
    LOG.debug('Create new role {name}. Role options: {behaviors} {images}'.format(**role_kwargs))
    role = IMPL.role.create(**role_kwargs)
    setattr(world, 'role', role['role'])


@step(r'I add created role to the farm')
def setting_farm(step):
    farm = world.farm
    branch = CONF.feature.to_branch
    release = branch in ['latest', 'stable']
    role_kwargs = dict(
        location=CONF.platforms[CONF.feature.platform]['location'] \
            if not CONF.feature.driver.is_platform_gce else "",
        options={
            "user-data.scm_branch": '' if release else branch,
            "base.upd.repository": branch if release else '',
            "base.devel_repository": '' if release else CONF.feature.ci_repo
        },
        alias=world.role['name'],
        use_vpc=USE_VPC
    )
    LOG.debug('Add created role to farm with options %s' % role_kwargs)
    farm.add_role(world.role['id'], **role_kwargs)
    farm.roles.reload()
    farm_role = farm.roles[0]
    setattr(world, '%s_role' % world.role['name'], farm_role)


@step(r'I trigger scalarizr update by Scalr UI')
def updating_scalarizr_by_scalr_ui(step):
    pass


@step(r'scalarizr version is valid in ([\w\d]+)$')
def asserting_version(step, serv_as):
    server = getattr(world, serv_as)
    pre_installed_agent = world.pre_installed_agent
    server.reload()
    command = 'scalarizr -v'
    # Windows handler
    if Dist.is_windows_family(CONF.feature.dist):
        res = world.run_cmd_command(server, command).std_out
    # Linux handler
    else:
        node = world.cloud.get_node(server)
        res = node.run(command, user=get_user_name())[0]
    assert re.findall('(Scalarizr [a-z0-9/./-]+)', res), "Can't get scalarizr version: %s" % res
    installed_agent = res.split()[1]
    LOG.debug('Scalarizr was updated from %s to %s' % (pre_installed_agent, installed_agent))
    assert LooseVersion(pre_installed_agent) != LooseVersion(installed_agent),\
        'Scalarizr version not valid, pre installed agent: %s, newest: %s' % (pre_installed_agent, installed_agent)


@step(r'I checkout to ([A-za-z0-9\/\-\_]+) from branch ([A-za-z0-9\/\-\_]+)$')
def forking_git_branch(step, branch_from, branch_to):
    pass