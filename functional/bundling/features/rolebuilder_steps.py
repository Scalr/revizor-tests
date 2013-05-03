import re
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Platform
from revizor2.api import IMPL
from revizor2.utils import wait_until


LOG = logging.getLogger('rolebuilder')


@step('I start build role$')
def start_rolebuild(step):
    location = CONF.platforms[CONF.main.platform]['location']
    if CONF.main.platform == 'rackspaceng':
        platform = 'rackspacengus'
    else:
        platform = CONF.main.platform
    os_family, os_version = re.findall(r'([a-zA-Z]+)(\d+)', CONF.main.dist)[0]
    if os_family == 'centos':
        images = IMPL.rolebuilder.images2()[CONF.main.platform]['images']
        for image in images:
            if image['os_family'] == os_family and image['os_version'].startswith(os_version) and \
                image['architecture'] == CONF.main.arch and image['cloud_location'] == location and not 'hvm' in image:
                os_version = image['os_version']
                break
    else:
        os_version = os_version[:2] + '.' + os_version[2:]
    bundle_id = IMPL.rolebuilder.build2(platform=platform,
                                        location=location,
                                        arch=CONF.main.arch,
                                        behaviors=CONF.main.behaviors,
                                        os_family=os_family,
                                        os_version=os_version,
                                        name='tmp-%s-%s-%s' % (CONF.main.platform, CONF.main.dist,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr=CONF.main.branch,)
    setattr(world, 'role_type', CONF.main.behaviors[0])
    setattr(world, 'bundle_id', bundle_id)


@step('I start build role with behaviors (.+)$')
def start_rolebuild(step, behaviors):
    behaviors = behaviors.strip().split(',')
    if not 'chef' in behaviors:
        behaviors.append('chef')
    location = CONF.platforms[CONF.main.platform]['location']
    if CONF.main.driver == Platform.GCE:
        location = 'all'
    platform = CONF.main.platform
    os_family, os_version = re.findall(r'([a-zA-Z]+)(\d+)', CONF.main.dist)[0]
    if os_family in ['centos', 'oel', 'rhel']:
        images = IMPL.rolebuilder.images2()[CONF.main.platform]['images']
        for image in images:
            if image['os_family'] == os_family and image['os_version'].startswith(os_version) and \
                image['architecture'] == CONF.main.arch and image['cloud_location'] == location and not 'hvm' in image \
                and image['root_device_type']=='ebs':
                os_version = image['os_version']
                break
    else:
        os_version = os_version[:2] + '.' + os_version[2:]
    bundle_id = IMPL.rolebuilder.build2(platform=platform,
                                        location=location,
                                        arch='x86_64',
                                        behaviors=behaviors,
                                        os_family=os_family,
                                        os_version=os_version,
                                        name='tmp-%s-%s-%s' % (CONF.main.platform, CONF.main.dist,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr='',
                                        mysqltype='percona' if 'percona' in behaviors else 'mysql')
    setattr(world, 'role_type', CONF.main.behaviors[0])
    setattr(world, 'bundle_id', bundle_id)


@step('Build task started')
def assert_build_started(step):
    logs = IMPL.bundle.logs(world.bundle_id)
    for l in logs:
        if 'Bundle task created' in l['message']:
            return True
    raise AssertionError('Not see pending status in bundletask %s' % world.bundle_id)


@step('Build task completed')
def assert_build_started(step):
    wait_until(world.bundle_task_complete_rolebuilder, args=(world.bundle_id,), timeout=2000,
               error_text='Bundletask %s is not completed' % world.bundle_id)


@step('I have new role id')
def assert_build_started(step):
    logs = IMPL.bundle.logs(world.bundle_id)
    for l in logs:
        if 'Role ID:' in l['message']:
            world.new_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
            return
    raise AssertionError('Not found new role id for bundletask %s' % world.bundle_id)
