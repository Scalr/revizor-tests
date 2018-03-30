import logging

from lettuce import world, step

LOG = logging.getLogger(__name__)
SERVICE_IGNORE_ERRORS = [
    "celery.worker.consumer.consumer: consumer: Cannot connect to amqp:"
]
LOG_PATH = {
    'csg': 'service/cloud-service-gateway.log'
}


@step('I set proxy for ([\w\d,]+) in Scalr to ([\w\d]+)')
def configure_scalr_proxy(step, clouds, proxy_as):
    clouds = [c.strip().lower() for c in clouds.split(',')]
    server = getattr(world, proxy_as)
    params = [
        {'name': 'scalr.connections.proxy.host', 'value': str(server.public_ip)},
        {'name': 'scalr.connections.proxy.port', 'value': 3128},
        {'name': 'scalr.connections.proxy.user', 'value': 'testuser'},
        {'name': 'scalr.connections.proxy.pass', 'value': 'p@ssw0rd'},
        {'name': 'scalr.connections.proxy.type', 'value': 0},
        {'name': 'scalr.connections.proxy.authtype', 'value': 1},
        {'name': 'scalr.connections.proxy.use_on', 'value': 'scalr'}
    ]
    for cloud in clouds:
        params.append(
            {'name': 'scalr.%s.use_proxy' % cloud, 'value': True}
        )
    LOG.debug('Proxy params:\n%s' % params)
    world.update_scalr_config(params)


@step('Scalr services( .+)? are in (\w+) state')
def check_scalr_service_status(step, services, state):
    services = services.split(',') if services else ['all']
    for service in services:
        statuses = world.testenv.get_service_status(name=service)
        for status in statuses:
            if status['state'].lower() != state.lower():
                raise AssertionError("Service %s status is %s. Expected status - %s" % (service, status, state))


@step('no "(.+)" in service "(\w+)" log')
def check_service_logs(step, search_string, service):
    ssh = world.testenv.get_ssh()
    LOG.debug("Check %s log for %s" % (service, search_string))
    out = ssh.run("cat /opt/scalr-server/var/log/service/%s.log | grep %s" % (service.strip(), search_string.strip()))
    if out[0]:
        errors = []
        logs = out[0].splitlines()
        for line in logs:
            if any(error in line for error in SERVICE_IGNORE_ERRORS) and line not in errors:
                errors.append(line)
        if errors:
            raise AssertionError("Found unexpected errors in %s service log. Errors:\n%s" % (service, errors))


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
