import logging

from lettuce import step, world


LOG = logging.getLogger(__name__)
LOG_PATH = {
    'csg': 'service/cloud-service-gateway.log'
}


@step("there are no (errors|warnings) in ([\w\d_-]+) log")
def verify_service_log(step, search_for, name):
    name = name.lower()
    if name not in LOG_PATH:
        raise ValueError('Invalid service: %s is not supported' % name)
    log_path = '/opt/scalr-server/var/log/%s' % LOG_PATH[name]
    LOG.info('Checking %s log in %s for %s' % (name, log_path, search_for))
    if search_for == 'errors':
        search_str = ' ERROR \|Traceback'
    else:
        search_str = ' ERROR \| WARNING \|Traceback'
    cmd = 'grep -n "%s" %s' % (search_str, log_path)
    result = world.testenv.get_ssh().run(cmd)[0]
    if result:
        raise AssertionError('Found issues in %s log: %s' % (name, result))
