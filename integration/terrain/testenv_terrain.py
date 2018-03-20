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
    search_strings = [' ERROR ', 'Traceback']
    if search_for == 'warnings':
        search_strings.append(' WARNING ')
    old_logs_count = getattr(world, '%s_testenv_logs_count' % name, 0)
    cmd = 'tail -n +%s %s' % (old_logs_count + 1, log_path)
    logs = world.testenv.get_ssh().run(cmd)[0].splitlines()
    setattr(world, '%s_testenv_logs_count' % name, len(logs) + old_logs_count)
    issues = []
    for string in search_strings:
        for line in logs:
            if string in line and line not in issues:
                issues.append(line)
    if issues:
        raise AssertionError('Found issues in %s log: %s' % (name, str(issues)))
