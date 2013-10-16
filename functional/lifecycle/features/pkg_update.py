import os
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Platform


LOG = logging.getLogger('pkg-update')


@step('I add role to this farm$')
def having_role_in_farm(step):
    role_type = os.environ.get('RV_BEHAVIOR', 'base')
    role = world.add_role_to_farm(role_type=role_type)
    LOG.info('Add role to farm %s' % role)
    world.role_type = role_type
    if not role:
        raise AssertionError('Error in add role to farm')
    setattr(world, world.role_type + '_role', role)
    world.role = role


@step('I change repo in ([\w\d]+)$')
def change_repo(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    repo = os.environ.get('RV_TO_BRANCH', 'master')
    if 'ubuntu' in node.os[0].lower():
        LOG.info('Change repo in Ubuntu')
        node.put_file('/etc/apt/sources.list.d/scalr-branch.list',
                                'deb http://buildbot.scalr-labs.com/apt/debian %s/\n' % repo)
    elif 'centos' in node.os[0].lower():
        LOG.info('Change repo in CentOS')
        node.put_file('/etc/yum.repos.d/scalr-stable.repo',
                                        '[scalr-branch]\n' +
                                        'name=scalr-branch\n' +
                                        'baseurl=http://buildbot.scalr-labs.com/rpm/%s/rhel/$releasever/$basearch\n' % repo +
                                        'enabled=1\n' +
                                        'gpgcheck=0\n' +
                                        'protect=1\n'
        )


@step('pin new repo in ([\w\d]+)$')
def pin_repo(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    repo = os.environ.get('RV_TO_BRANCH', 'master')
    if 'ubuntu' in node.os[0].lower():
        LOG.info('Pin repo %s in Ubuntu' % repo)
        node.put_file('/etc/apt/preferences',
                                'Package: *\n' +
                                'Pin: release a=%s\n' % repo +
                                'Pin-Priority: 990\n'
        )
    elif 'centos' in node.os[0].lower():
        LOG.info('Pin repo %s in CentOS' % repo)
        node.run('yum install yum-protectbase -y')


@step('update scalarizr in ([\w\d]+)$')
def update_scalarizr(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if 'ubuntu' in node.os[0].lower():
        LOG.info('Update scalarizr in Ubuntu')
        node.run('apt-get update')
        node.run('apt-get install scalarizr-base scalarizr-%s -y' % Platform.to_scalr(CONF.main.driver))
    elif 'centos' in node.os[0].lower():
        LOG.info('Update scalarizr in CentOS')
        node.run('yum install scalarizr-base scalarizr-%s -y' % Platform.to_scalr(CONF.main.driver))
