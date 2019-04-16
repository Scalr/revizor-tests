import re
import time
import logging

from lettuce import world, step

LOG = logging.getLogger(__name__)


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


@step('I wait server ([\w\d,]+) in (\w+) state')
def multiple_bootstrapping(step, servers, state):
    servers = servers.split(',')
    for server in servers:
        LOG.debug("Checking server %s in multistep" % server)
        step.behave_as("I wait server %s in %s state" % (server, state))


@step("not ERROR in ([\w\d,]+) scalarizr log")
def multiple_servers_log_check(step, servers):
    servers = servers.split(',')
    for server in servers:
        step.behave_as("not ERROR in %s scalarizr log" % server)


@step(r'agent stat for ([\w\d,]+) is collected via (Pulling|Pushing)$')
def check_pulling_or_pushing(step, serv_as, method):
    # NOTE: migrated
    serv_as = serv_as.split(',')
    servers = [getattr(world, s) for s in serv_as]
    LOG.debug("Servers: %s" % servers)
    regex = "server.apps.monitor: Received message: ({(?:.+)?'type': 'agent-stat'(?:.+)?})"  # Search criteria for Pushing
    for server in servers:
        LOG.debug("Check %s mechanism for %s" % (method, server.id))
        search_string = 'server.tasks.monitor.health: Server %s agent_stat is {' % server.id  # Search criteria for Pulling
        success = False
        for i in range(10):
            LOG.debug("%s attempt to get agent_stat message" % i)
            monitor_log = world.testenv.get_ssh().run('cat /opt/scalr-server/var/log/service/monitor.log')[0]
            if monitor_log:
                if method == 'Pulling':
                    if search_string in monitor_log:
                        success = True
                else:
                    messages = re.findall(regex, monitor_log)
                    LOG.debug("Pushing messages:\n%s" % messages)
                    for message in messages:
                        if server.id in message:
                            success = True
                            break
            if success:
                break
            time.sleep(5)
        if not success:
            raise AssertionError('%s message for server %s was not found in monitor log!' % (method, server.id))


@step(r'data for ([\w\d,]+) is present in influx')
def verify_influx(step, servers):
    # NOTE: migrated
    ssh = world.testenv.get_ssh()
    influx_command = re.search("alias influx='(.+)'", ssh.run('cat ~/.bashrc')[0]).group(1)
    LOG.debug("Influx command %s" % influx_command)
    if not influx_command:
        raise AssertionError("Can't find influx alias on TestEnv %s" % world.testenv.te_id)
    servers = [getattr(world, s) for s in servers.split(',')]
    for server in servers:
        cmd = """%s -execute "select * from "week".stat_memory_cpu where farm_role_id = '%s' and farm_id = '%s' and server_index = '%s'" -database='scalr'""" % (influx_command,
            server.farm_role.id, server.farm.id, server.index)
        LOG.debug("Try to get influx data for server %s.\n Command - %s" % (server.id, cmd))
        out = ssh.run(cmd)
        if not out[0]:
            raise AssertionError("Can't get influx data for server %s. Error - %s" % (server.id, out[1]))
        LOG.debug("Influx command output:\n%s" % (out[0]))
