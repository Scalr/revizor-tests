import logging

from lettuce import world, step

LOG = logging.getLogger(__name__)

SERVICE_IGNORE_ERRORS = [
    "celery.worker.consumer.consumer: consumer: Cannot connect to amqp:"
]


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
