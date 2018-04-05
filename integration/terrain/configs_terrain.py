import os

from lettuce import world, step

from revizor2.api import Cloud
from revizor2.conf import CONF
from revizor2.consts import Dist, Platform


@step('I have configured revizor environment:')
def configure_revizor(step):
    for revizor_opt in step.hashes:
        os.environ['RV_%s' % revizor_opt['name'].upper()] = revizor_opt['value']
        CONF.feature[revizor_opt['name']] = revizor_opt['value']
        if revizor_opt['name'] == 'platform':
            CONF.feature.platform = Platform(os.environ.get('RV_PLATFORM', 'gce'))
            world.cloud = Cloud(os.environ.get('RV_PLATFORM', 'gce'))
        elif revizor_opt['name'] == 'dist':
            CONF.feature.dist = Dist(os.environ.get('RV_DIST', 'ubuntu1604'))


@step('I have configured scalr config')
def configure_scalr_config(step):
    world.update_scalr_config(step.hashes)


@step('I (restart|stop|start) service "([\w\d_-]+)"')
def service_control(step, action, service_name):
    getattr(world.testenv, '%s_service' % action)(service_name)
