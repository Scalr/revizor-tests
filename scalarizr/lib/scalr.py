import logging

from revizor2.utils import get_dict_value


LOG = logging.getLogger(__name__)


def update_scalr_config(testenv, params):
    config = testenv.get_config()
    for param in params.keys():
        config_group, config_name = param.rsplit('.', 1)
        value = get_dict_value(config, str(config_group))
        value[str(config_name)] = params[param]
    testenv.put_config(config)


def get_scalr_config_value(testenv, param):
    config = testenv.get_config()
    return get_dict_value(config, param)


def configure_scalr_proxy(testenv, server, modules):
    modules = [m.strip().lower() for m in modules.split(',')]
    params = {
        'scalr.connections.proxy.host': str(server.public_ip),
        'scalr.connections.proxy.port': 3128,
        'scalr.connections.proxy.user': 'testuser',
        'scalr.connections.proxy.pass': 'p@ssw0rd',
        'scalr.connections.proxy.type': 0,
        'scalr.connections.proxy.authtype': 1,
        'scalr.connections.proxy.use_on': 'scalr'
    }
    for module in modules:
        params.update(
            {'scalr.%s.use_proxy' % str(module): 'true'}
        )
    LOG.debug('Proxy params:\n%s' % params)
    update_scalr_config(testenv, params)
