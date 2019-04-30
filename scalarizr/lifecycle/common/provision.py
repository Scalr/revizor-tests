import re
import time
import logging

import chef
from revizor2 import api
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.cloud import Cloud, ExtendedNode

from scalarizr.lib import server as lib_server
from scalarizr.lib import farm as lib_farm


LOG = logging.getLogger(__name__)


def get_chef_bootstrap_stat(node: ExtendedNode):
    # Get chef client.pem update time
    bootstrap_stat = node.run('stat -c %Y /etc/chef/client.pem').std_out.split()[0]
    LOG.debug(f'Chef client.pem, last modification time: {bootstrap_stat}')
    return bootstrap_stat


def check_process_status(node: ExtendedNode, process: str, work: bool = False):
    LOG.info(f"Check running process {process} on server")
    list_proc = node.run('ps aux | grep %s' % process).std_out.split('\n')
    processes = filter(lambda x: 'grep' not in x and x, list_proc)
    msg = f"Process {process} on server {node.id} not in valid state"
    assert not processes if work else processes, msg


def assert_chef_node_name_equal_hostname(cloud: Cloud, server: api.Server):
    hostname = lib_server.get_hostname_by_server_format(server)
    node = cloud.get_node(server)
    command = CONF.feature.dist.is_windows \
        and 'findstr node_name c:\\chef\\client.rb' \
        or 'cat /etc/chef/client.rb | grep node_name'
    with node.remote_connection() as conn:
        result = conn.run(command).std_out
        node_name = result.strip().split()[1][1:-1]
        if not node_name == hostname:
            raise AssertionError(f'Chef node_name "{node_name}" != hostname on server "{hostname}"')


def assert_chef_log_contains_text(server: api.Server, pattern: str):
    server.scriptlogs.reload()
    log_lable = '[Scalr built-in] Chef bootstrap'
    chef_log = list(filter(lambda l: l.name == log_lable, server.scriptlogs))
    if not(chef_log and pattern in chef_log[0].message or False):
        raise AssertionError(f'Text "{pattern}" not found in chef bootstrap:\n{chef_log}')


def assert_node_exists_on_chef_server(server: api.Server, exist: bool = True):
    # NOTE: migrated
    hostname = lib_server.get_hostname_by_server_format(server)
    LOG.debug(f'Chef node name: {hostname}')

    chef_api = chef.autoconfigure()

    if not isinstance(chef_api, chef.api.ChefAPI):
        raise AssertionError("Can't initialize ChefAPI instance.")

    node = chef.Node(hostname, api=chef_api)

    if node.exists != exist:
        raise AssertionError(f'Server {server.id} with hostname {hostname} in state {node.exists} '
                             f'on Chef server but need: {exist}')


def wait_for_farm_state(farm: api.Farm, state):
    """Wait for state of farm"""
    wait_until(lib_farm.get_farm_state, args=(farm, state),
               timeout=300, error_text=f'Farm not in status {state}')


def remove_file_on_win(node: ExtendedNode, filename: str):
    cmd = f'del /F {filename}'
    res = node.run(cmd)
    assert not res.std_err, f"An error occurred while try to delete {filename}:\n{res.std_err}"


def change_chef_client_interval_value(node: ExtendedNode, interval: int):
    node.run(f'echo -e "INTERVAL={interval}" >> /etc/default/chef-client')
    node.run("systemctl restart chef-client")


def assert_chef_client_interval_value(node: ExtendedNode, interval: int):
    res = node.run("systemctl status chef-client")
    assert not res.std_err, f'Error on chef-client, ended with code: [{res.status_code}].\n{res.std_err}'
    assert f'chef-client -i {interval}' in res.std_out


def assert_chef_runs_time(node: ExtendedNode, interval: int):
    interval = int(interval) * 3
    time.sleep(interval)
    res = node.run("systemctl status chef-client")
    active_line = res.std_out.splitlines()[2]
    match = re.search('(?:(\d+)min)? (\d+)s', active_line)
    minutes = match.group(1)
    seconds = int(match.group(2))
    runtime = minutes and (int(minutes) * 60) or seconds
    assert int(runtime) > interval


def assert_script_data_deleted(cloud: Cloud, server: api.Server):
    node = cloud.get_node(server)
    server.scriptlogs.reload()
    LOG.info('Check script executed data was deleted')
    if not server.scriptlogs:
        raise AssertionError("No orchestration logs found on %s" % server.id)
    task_dir = server.scriptlogs[0].execution_id.replace('-', '')
    cmd = CONF.feature.dist.is_windows \
        and f'dir c:\\opt\\scalarizr\\var\\lib\\tasks\\{task_dir} /b /s /ad | findstr /e "\\bin \\data"' \
        or f'find /var/lib/scalarizr/tasks/{task_dir} -type d -regex ".*/\\(bin\\|data\\)"'
    with node.remote_connection() as conn:
        result = conn.run(cmd)
        assert not result.status_code, f"Command: {cmd} execution error:\n {result.std_err}"
        folders = [l for l in result.std_out.splitlines() if l.strip()]
        assert not folders,  f"Find script data {folders} on {server.id}"


def assert_chef_bootstrap_failed(cloud: Cloud, server: api.Server):
    node = cloud.get_node(server)
    assertion_msg = "Chef bootstrap marker not found in scalarizr_debug.log"
    if CONF.feature.dist.is_windows:
        failure_marker = 'chef-client" exited with code 1'
        cmd = 'findstr /C:"Command \\"C:\opscode\chef\\bin\chef-client\\" exited with code 1"' \
              ' "C:\opt\scalarizr\\var\log\scalarizr_debug.log"'
        assert failure_marker in node.run(cmd).std_out, assertion_msg
    else:
        failure_markers = [
            'Command "/usr/bin/chef-client" exited with code 1',
            'Command /usr/bin/chef-client exited with code 1']
        assert any(node.run(f'grep {m} /var/log/scalarizr_debug.log').std_out.strip() for m in failure_markers), \
            assertion_msg
