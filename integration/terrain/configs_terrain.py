import os
import functools

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.consts import Platform


def get_dict_value(obj, key):
    def dict_get(d, key):
        if key not in d:
            d[key] = {}
        return d.get(key, {})

    return functools.reduce(dict_get, key.split('.'), obj)


@step('I have configured revizor environment:')
def configure_revizor(step):
    for revizor_opt in step.hashes:
        os.environ['RV_%s' % revizor_opt['name'].upper()] = revizor_opt['value']
        CONF.feature[revizor_opt['name']] = revizor_opt['value']
        if revizor_opt['name'] == 'platform':
            CONF.feature.driver = Platform((CONF.platforms[CONF.feature.platform]['driver']))


@step('Given I have configured scalr config')
def configure_scalr_config(step):
    config = world.testenv.get_config()
    for opt in step.hashes:
        config_group, config_name = opt['name'].rsplit('.', 1)
        value = get_dict_value(config, str(config_group))
        value[str(config_name)] = str(opt['value'])
    world.testenv.put_config(config)


@step('I (restart|stop|start) service "([\w\d_]+)"')
def service_control(step, action, service_name):
    getattr(world.testenv, '%s_service' % action)(service_name)
