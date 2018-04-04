import logging

from lettuce import world, step

from revizor2.api import Cloud

LOG = logging.getLogger(__name__)
SERVICE_IGNORE_ERRORS = [
    "celery.worker.consumer.consumer: consumer: Cannot connect to amqp:"
]
LOG_PATH = {
    'csg': 'service/cloud-service-gateway.log'
}


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
