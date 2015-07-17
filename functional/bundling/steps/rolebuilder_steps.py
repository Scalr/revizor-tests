import re
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.api import IMPL
from revizor2.conf import CONF
from revizor2.fixtures import images
from revizor2.utils import wait_until
from revizor2.consts import Platform, Dist


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
def start_rolebuild(step, behaviors):
    behaviors = behaviors.strip().split(',')
    if not 'chef' in behaviors:
        behaviors.append('chef')
    location = CONF.platforms[CONF.feature.platform]['location']
    if CONF.feature.driver.current_cloud == Platform.GCE:
        location = 'all'
    platform = CONF.feature.driver.scalr_cloud
    os_id = Dist.get_os_id(CONF.feature.dist)
    if CONF.feature.driver.current_cloud in (Platform.GCE, Platform.ECS):
        image = filter(lambda x: x['os_id']==os_id,
                       images(Platform.to_scalr(CONF.feature.driver.current_cloud)).all()['images'])[0]
    else:
        image = filter(lambda x: x['cloud_location']==CONF.platforms[CONF.feature.platform]['location'] and
                             x['os_id']==os_id,
                       images(CONF.feature.driver.scalr_cloud).all()['images'])[0]
    bundle_id = IMPL.rolebuilder.build2(platform=platform,
                                        location=location,
                                        arch='x86_64',
                                        behaviors=behaviors,
                                        os_id=image['os_id'],
                                        name='tmp-%s-%s-%s' % (CONF.feature.platform, CONF.feature.dist,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr=CONF.feature.branch,
                                        mysqltype='percona' if 'percona' in behaviors else 'mysql',
                                        hvm = True if CONF.feature.dist == 'amzn1503' else False)
    setattr(world, 'role_type', CONF.feature.behaviors[0])
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
            world.bundled_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
            LOG.info('New bundled role id is: %s' % world.bundled_role_id)
            return
    raise AssertionError('Not found new role id for bundletask %s' % world.bundle_id)
