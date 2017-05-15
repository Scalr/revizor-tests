import re
import os
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.api import IMPL, Server, Cloud
from revizor2.conf import CONF
from revizor2.fixtures import images
from revizor2.utils import wait_until
from revizor2.exceptions import NotFound
from revizor2.consts import Platform, Dist


LOG = logging.getLogger('rolebuilder')


@step('I start build role with behaviors (.+)$')
def start_rolebuild_with_behaviours(step, behaviors):
    behaviors = behaviors.strip().split(',')

    if not 'chef' in behaviors:
        behaviors.append('chef')

    if CONF.feature.driver.current_cloud not in (Platform.EC2, Platform.CLOUDSTACK) and 'mongodb' in behaviors:
        raise AssertionError('Mongodb not supported in this platform')

    location = CONF.platforms[CONF.feature.platform]['location']
    if CONF.feature.driver.current_cloud == Platform.GCE:
        location = 'all'
    platform = CONF.feature.driver.scalr_cloud
    os_id = CONF.feature.dist.id
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
                                        terminate=False,
                                        arch='x86_64',
                                        behaviors=behaviors,
                                        os_id=image['os_id'],
                                        name='tmp-%s-%s-%s' % (CONF.feature.platform, CONF.feature.dist.id,
                                                               datetime.now().strftime('%m%d-%H%M')),
                                        scalarizr=CONF.feature.branch,
                                        mysqltype='percona' if 'percona' in behaviors else 'mysql')
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
        test_name = step.scenario.described_at.file.split('/')[-1].split('.')[0]
        path = os.path.realpath(os.path.join(CONF.main.log_path, 'scalarizr',
                                             test_name,
                                             world.test_start_time.strftime('%m%d-%H:%M'),
                                             step.scenario.name.replace('/', '-'),
                                             rolebuilder_server.id + '-role-builder.log.gz'))
        LOG.debug('Path to save log: %s' % path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), 0755)
        rolebuilder_server.get_logs('../role-builder.log', path, compress=True)
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
