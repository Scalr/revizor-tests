import re
import os
from datetime import datetime
import logging

from lettuce import world, step, after, before

from revizor2.api import IMPL, Server, Cloud
from revizor2.conf import CONF
from revizor2.fixtures import images
from revizor2.utils import wait_until
from revizor2.exceptions import NotFound
from revizor2.consts import Platform, Dist
from revizor2.defaults import DEFAULT_AMAZON_VPC


LOG = logging.getLogger('rolebuilder')


@step('I start build role$')
def start_rolebuild(step):
    location = CONF.platforms[CONF.feature.platform]['location']
    if CONF.feature.platform == 'rackspaceng':
        platform = 'rackspacengus'
    else:
        platform = CONF.feature.platform
    os_id = Dist.get_os_id(CONF.feature.dist)
    image = filter(lambda x: x['cloud_location'] == CONF.platforms[CONF.feature.platform]['location']
                             and x['os_id']==os_id,
                   images(CONF.feature.driver.scalr_cloud).all()['images'])[0]
    bundle_id = IMPL.rolebuilder.build2(platform=platform,
                                        location=location,
                                        arch='x86_64',
                                        behaviors=CONF.feature.behaviors,
                                        os_id=image['os_id'],
                                        os_version=image['os_version'],
                                        name='tmp-%s-%s-%s' % (CONF.feature.platform, CONF.feature.dist,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr=CONF.feature.branch,)
    setattr(world, 'role_type', CONF.feature.behaviors[0])
    setattr(world, 'bundle_id', bundle_id)


@step('I start build role with behaviors (.+)$')
def start_rolebuild_with_behaviours(step, behaviors):
    behaviors = behaviors.strip().split(',')
    use_hvm = False

    if not 'chef' in behaviors:
        behaviors.append('chef')

    if DEFAULT_AMAZON_VPC:
        use_hvm = True
        if 'mongodb' in behaviors:
            behaviors.remove('mongodb')

    if CONF.feature.driver.current_cloud not in (Platform.EC2, Platform.CLOUDSTACK) and 'mongodb' in behaviors:
        raise AssertionError('Mongodb not supported in this platform')

    location = CONF.platforms[CONF.feature.platform]['location']
    if CONF.feature.driver.current_cloud == Platform.GCE:
        location = 'all'
    platform = CONF.feature.driver.scalr_cloud
    os_id = Dist.get_os_id(CONF.feature.dist)
    try:
        if CONF.feature.driver.current_cloud in (Platform.GCE, Platform.ECS):
            image = filter(lambda x: x['os_id'] == os_id,
                           images(Platform.to_scalr(CONF.feature.driver.current_cloud)).all()['images'])[0]
        else:
            image = filter(lambda x: x['cloud_location'] == CONF.platforms[CONF.feature.platform]['location'] and
                                 x['os_id'] == os_id,
                           images(CONF.feature.driver.scalr_cloud).all()['images'])[0]
    except IndexError:
        raise NotFound('Image for os "%s" not found in rolebuilder!' % os_id)
    bundle_id = IMPL.rolebuilder.build2(platform=platform,
                                        location=location,
                                        arch='x86_64',
                                        behaviors=behaviors,
                                        os_id=image['os_id'],
                                        name='tmp-%s-%s-%s' % (CONF.feature.platform, CONF.feature.dist,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr=CONF.feature.branch,
                                        mysqltype='percona' if 'percona' in behaviors else 'mysql',
                                        hvm = use_hvm)
    setattr(world, 'role_type', CONF.feature.behaviors[0])
    setattr(world, 'bundle_id', bundle_id)


@step('Build task started')
def assert_build_started(step):
    logs = IMPL.bundle.logs(world.bundle_id)
    for l in logs:
        if 'Bundle task created' in l['message']:
            rolebuilder_server_id = re.search('ServerID: ((\w+-)+\w+),', l['message']).group(1)
            rolebuilder_server = Server(**IMPL.server.get(rolebuilder_server_id))
            setattr(world, 'rolebuilder_server', rolebuilder_server)
            return True
    raise AssertionError('Not see pending status in bundletask %s' % world.bundle_id)


@step('Build task completed')
def assert_build_completed(step):
    try:
        wait_until(world.bundle_task_complete_rolebuilder, args=(world.bundle_id,), timeout=2000,
                   error_text='Bundletask %s is not completed' % world.bundle_id)
    except BaseException as e:
        rolebuilder_server = world.rolebuilder_server
        path = os.path.realpath(os.path.join(CONF.main.log_path, 'scalarizr',
                                             'rolebuilder',
                                             rolebuilder_server.id + '-role-builder.log'))
        LOG.debug('Path to save log: %s' % path)
        if not os.path.exists(path):
            os.makedirs(path, 0755)
        rolebuilder_server.get_logs('../role-builder.log', path)
        rolebuilder_server.terminate()
        raise e


@step('I have new role id')
def assert_role_created(step):
    logs = IMPL.bundle.logs(world.bundle_id)
    for l in logs:
        if 'Role ID:' in l['message']:
            world.bundled_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
            LOG.info('New bundled role id is: %s' % world.bundled_role_id)
            return
    raise AssertionError('Not found new role id for bundletask %s' % world.bundle_id)
