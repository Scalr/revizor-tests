import re
import time
import logging

from lettuce import world, step

from revizor2.api import Cloud

LOG = logging.getLogger(__name__)


@step("I configure roles in testenv")
def configure_roles_in_testenv(step):
    for role_opts in step.hashes:
        step.behave_as("""
            And I have configured revizor environment:
                | name           | value       |
                | platform       | {platform}  |
                | dist           | {dist}      |
                | branch         | {branch}    |
                | ci_repo        | {ci_repo}   |
            And I add role to this farm
            Then I see pending server {index}""".format(
                    platform=role_opts['platform'],
                    dist=role_opts['dist'],
                    branch=role_opts['branch'],
                    ci_repo=role_opts['ci_repo'],
                    index=role_opts['server_index']))


@step('I wait server ([\w\d,]+) in (\w+) state')
def multiple_bootstrapping(step, servers, state):
    servers = servers.split(',')
    for server in servers:
        step.behave_as("I wait server %s in %s state" % (server, state))


@step("not ERROR in ([\w\d,]+) scalarizr log")
def multiple_servers_log_check(step, servers):
    servers = servers.split(',')
    for server in servers:
        step.behave_as("not ERROR in %s scalarizr log" % server)


@step(r'agent stat for ([\w\d,]+) is collected via (Pulling|Pushing)$')
def check_pulling_or_pushing(step, serv_as, method):
    serv_as = serv_as.split(',')
    servers = [getattr(world, s) for s in serv_as]
    LOG.debug("Servers: %s" % servers)
    for server in servers:
        LOG.debug("Check %s for %s" % (method, server.id))
        regex = "server.apps.monitor: Received message: ({(?:.+)?'type': 'agent-stat'(?:.+)?})"  # Search criteria for Pushing
        search_string = 'server.tasks.monitor.health: Server %s agent_stat is {' % server.id  # Search criteria for Pulling
        for i in range(10):
            LOG.debug("%s attempt to get agent_stat message" % i)
            monitor_log = world.testenv.get_ssh().run('cat /opt/scalr-server/var/log/service/monitor.log')[0]
            if monitor_log:
                if method == 'Pulling':
                    if search_string in monitor_log:
                        return True
                else:
                    messages = re.findall(regex, monitor_log)
                    LOG.debug("Pushing messages:\n%s" % messages)
                    for message in messages:
                        if server.id in message:
                            return True
            time.sleep(5)
        raise AssertionError('%s message for server %s was not found in monitor log!' % (method, server.id))


@step(r'proxy ([\w\d]+) log contains message "(.+)"$')
def verify_proxy_working(step, proxy_as, message):
    server = getattr(world, proxy_as)
    proxy_cloud = Cloud(server.platform)
    node = proxy_cloud.get_node(server)
    logs = node.run("cat /var/log/squid3/access.log").std_out
    if message not in logs:
        raise AssertionError("No messages indicating that proxy is working were found in log!")
