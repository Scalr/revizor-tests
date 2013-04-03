import os
import re
import time
from datetime import datetime
import logging

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.api import Farm, IMPL
from revizor2.consts import ServerStatus
from revizor2.utils import wait_until


LOG = logging.getLogger('rolebuilder')


@step('I start build role')
def start_rolebuild(step):
    location = 'us-east-1'
    if CONF.main.platform == 'rackspace':
        location = 'rs-ORD1'
    bundle_id = IMPL.role_build(platform=CONF.main.platform,
                                                            location=location,
                                architecture=CONF.main.arch,
                                                            behaviors=CONF.main.behaviors,
                                os=CONF.main.dist,
                                role_name='tmp-%s-%s-%s' % (CONF.main.platform, CONF.main.dist,
                                                               datetime.now().strftime('%m%d')),
                                scalarizr=CONF.main.branch,
                                                    )
    setattr(world, 'role_type', CONF.main.behaviors[0])
    setattr(world, 'bundle_id', bundle_id)


@step('Build task started')
def assert_build_started(step):
    logs = IMPL.bundletask_get_logs(world.bundle_id)
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
    logs = IMPL.bundletask_get_logs(world.bundle_id)
    for l in logs:
        if 'Role ID:' in l['message']:
            world.new_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
            return
    raise AssertionError('Not found new role id for bundletask %s' % world.bundle_id)
