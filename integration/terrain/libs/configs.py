from lettuce import world

from revizor2.utils import get_dict_value


@world.absorb
def update_scalr_config(params):
    config = world.testenv.get_config()
    for param in params:
        config_group, config_name = param['name'].rsplit('.', 1)
        value = get_dict_value(config, str(config_group))
        value[str(config_name)] = param['value']
    world.testenv.put_config(config)


@world.absorb
def get_scalr_config_value(param):
    config = world.testenv.get_config()
    return get_dict_value(config, param)