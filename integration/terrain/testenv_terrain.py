import logging

from lettuce import world, step

from revizor2.api import Cloud

LOG = logging.getLogger(__name__)

SERVICE_IGNORE_ERRORS = [
    "celery.worker.consumer.consumer: consumer: Cannot connect to amqp:"
]


@step('I set proxy for ([\w\d,.]+) in Scalr to ([\w\d]+)')
def configure_scalr_proxy(step, modules, proxy_as):
    modules = [m.strip().lower() for m in modules.split(',')]
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
    for module in modules:
        params.append(
            {'name': 'scalr.%s.use_proxy' % str(module), 'value': True}
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


@step('no "(.+)" in service "(.+)" log')
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


@step("I configure roles in testenv")
def configure_roles_in_testenv(step):
    index = 0
    for role_opts in step.hashes:
        step.behave_as("""
            And I have configured revizor environment:
                | name           | value       |
                | platform       | {platform}  |
                | dist           | {dist}      |
                | branch         | {branch}    |
                | ci_repo        | {ci_repo}   |
            And I add role to this farm""".format(
                platform=role_opts['platform'],
                dist=role_opts['dist'],
                branch=role_opts['branch'],
                ci_repo=role_opts['ci_repo']))
        role = world.farm.roles[index]
        state = 'pending'
        timeout = 1400
        server = world.wait_server_bootstrapping(role, state, timeout)
        setattr(world, role_opts['server_index'], server)
        LOG.info('Server %s (%s) successfully in %s state' % (server.id, role_opts['server_index'], state))
        index += 1


@step(r'proxy ([\w\d]+) log contains message "(.+)"(?: for ([\w\d]+))?')
def verify_proxy_working(step, proxy_as, message, serv_as):
    proxy = getattr(world, proxy_as)
    proxy_cloud = Cloud(proxy.platform)
    node = proxy_cloud.get_node(proxy)
    logs = node.run("cat /var/log/squid3/access.log").std_out
    if serv_as:
        server = getattr(world, serv_as)
        message = message + " %s:443" % server.public_ip
    if message not in logs:
        raise AssertionError("No messages indicating that proxy is working were found in log!")
