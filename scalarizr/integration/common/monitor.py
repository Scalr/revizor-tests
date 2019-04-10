import re
import time
import logging


LOG = logging.getLogger(__name__)


def assert_stats_received(servers: dict, testenv, method: str):
    servers = list(servers.values())
    push_regex = "server.monitor.app: Received message: ({(?:.+)?'type': 'agent-stat'(?:.+)?})"  # Search criteria for
    # Pushing
    for server in servers:
        LOG.debug(f"Check {method} mechanism for {server.id}")
        pull_str = 'server.tasks.monitor.health: Server %s agent_stat is {' % server.id  # Search criteria for
        # Pulling
        success = False
        for i in range(10):
            LOG.debug(f"{i} attempt to get agent_stat message")
            monitor_log = testenv.get_ssh().run('cat /opt/scalr-server/var/log/service/monitor.log')[0]
            if monitor_log:
                if method == 'Pulling':
                    if pull_str in monitor_log:
                        success = True
                else:
                    messages = re.findall(push_regex, monitor_log)
                    LOG.debug(f'Find server_id {server.id} in log')
                    for message in messages:
                        if server.id in message:
                            success = True
                            break
            if success:
                break
            time.sleep(5)
        if not success:
            raise AssertionError(f'{method} message for server {server.id} was not found in monitor log!')


def assert_push_stats_in_influx(testenv, servers: dict):
    ssh = testenv.get_ssh()
    influx_command = re.search("alias influx='(.+)'", ssh.run('cat ~/.bashrc')[0]).group(1)
    LOG.debug(f"Influx command {influx_command}")
    if not influx_command:
        raise AssertionError(f"Can't find influx alias on TestEnv {testenv.te_id}")
    servers = servers.values()
    for server in servers:
        cmd = """%s -execute "select * from "week".stat_memory_cpu where farm_role_id = '%s' and farm_id = '%s' and 
        server_index = '%s'" -database='scalr'""" % (
        influx_command,
        server.farm_role.id, server.farm.id, server.index)
        LOG.debug("Try to get influx data for server %s.\n Command - %s" % (server.id, cmd))
        out = ssh.run(cmd)
        if not out[0]:
            raise AssertionError("Can't get influx data for server %s. Error - %s" % (server.id, out[1]))
        LOG.debug("Influx command output:\n%s" % (out[0]))
