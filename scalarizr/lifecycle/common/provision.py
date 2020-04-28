import re
import time
import logging

#FIXME: Chef not work on os x 10.15 and new python
# import chef

from tower_cli import get_resource as at_get_resource
from tower_cli.conf import settings as at_settings
from typing import Mapping

from revizor2 import api
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.cloud import Cloud, ExtendedNode
from revizor2.backend import IMPL

from scalarizr.lib import server as lib_server
from scalarizr.lib import farm as lib_farm


LOG = logging.getLogger(__name__)

AT_CONFIG = CONF.credentials.ansible_tower


def get_chef_bootstrap_stat(node: ExtendedNode):
    # Get chef client.pem update time
    bootstrap_stat = node.run('stat -c %Y /etc/chef/client.pem').std_out.split()[0]
    LOG.debug(f'Chef client.pem, last modification time: {bootstrap_stat}')
    return bootstrap_stat


def get_chef_bootstrap_logs(server: api.Server):
    server.scriptlogs.reload()
    log_lable = '[Scalr built-in] Chef bootstrap'
    return list(filter(lambda l: l.name == log_lable, server.scriptlogs))


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
    chef_log = get_chef_bootstrap_logs(server)
    if not(chef_log and pattern in chef_log[0].message or False):
        raise AssertionError(f'Text "{pattern}" not found in chef bootstrap:\n{chef_log}')


def assert_chef_log_not_contains_level(server: api.Server, log_levels: Mapping[str, list]):
    if not isinstance(log_levels, list):
        log_levels = [log_levels]
    chef_log = get_chef_bootstrap_logs(server)
    logs = chef_log and chef_log[0].message or None
    if not logs or any(level in logs for level in log_levels):
        raise AssertionError(f"Log is empty or one of log levels: {log_levels} found in chef bootstrap:\n{logs}")


# def assert_node_exists_on_chef_server(server: api.Server, exist: bool = True):
#     # NOTE: migrated
#     hostname = lib_server.get_hostname_by_server_format(server)
#     LOG.debug(f'Chef node name: {hostname}')
#
#     chef_api = chef.autoconfigure()
#
#     if not isinstance(chef_api, chef.api.ChefAPI):
#         raise AssertionError("Can't initialize ChefAPI instance.")
#
#     node = chef.Node(hostname, api=chef_api)
#
#     if node.exists != exist:
#         raise AssertionError(f'Server {server.id} with hostname {hostname} in state {node.exists} '
#                              f'on Chef server but need: {exist}')


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
    node.run("service chef-client restart ")


def assert_chef_client_interval_value(node: ExtendedNode, interval: int):
    res = node.run("service chef-client status")
    assert not res.std_err, f'Error on chef-client, ended with code: [{res.status_code}].\n{res.std_err}'
    assert f'chef-client -i {interval}' in res.std_out


def assert_chef_runs_time(node: ExtendedNode, interval: int):
    interval = int(interval) * 3
    time.sleep(interval)
    res = node.run("service chef-client status")
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
    if CONF.feature.dist.is_windows:
        cmd = f'dir c:\\opt\\scalarizr\\var\\lib\\tasks\\{task_dir} /b /s /ad | findstr /e "\\bin \\data"'
    else:
        cmd = f'find /var/lib/scalarizr/tasks/{task_dir} -type d -regex ".*/\\(bin\\|data\\)"'
    with node.remote_connection() as conn:
        result = conn.run(cmd)
        assert not result.std_err, f"Command: {cmd} execution error:\n {result.std_err}"
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


def set_at_server_id(context: dict):
    at_servers_list = IMPL.ansible_tower.list_servers()
    at_server_id = at_servers_list['servers'][0]['id']
    assert at_server_id, 'The Ansible-Tower server Id was not found'
    context['at_server_id'] = at_server_id


def create_copy_at_inventory(context: dict, inventory_name: str):
    """
    I create a copy of the inventory for each run of the test.
    This is required to parallel the execution of jobs in running tests.
    """
    new_name = f'{CONF.feature.dist.id}-{time.strftime("%H:%M:%S:%MS")}'
    kwargs = {'description': new_name}
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('inventory')
        inventory = list(filter(
            lambda i: i['name'] == inventory_name,
            res.list(all_pages=True)['results']))
        assert inventory, f'Inventory: {inventory_name} not found on AT server'
        at_res_copy = res.copy(pk=inventory[0]['id'], new_name=new_name, **kwargs)
        assert new_name in at_res_copy['description'], \
            f'Inventory was not found in Ansible Tower. Response from server: {at_res_copy}.'
        context['at_inventory_id'] = at_res_copy['id']
        context['at_inventory_name'] = at_res_copy['name']


def create_at_group(context: dict, group_type: str, group_name: str):
    """
    :param group_type: You can set 'regular' or 'template' type.
    """
    group_name = f'{group_name}-{time.strftime("%a-%d-%b-%Y-%H:%M:%S:%MS")}'
    at_group = IMPL.ansible_tower.create_inventory_groups(
        group_name,
        group_type,
        context['at_server_id'],
        context['at_inventory_id'])

    context['at_group_type'] = group_type
    context['at_group_name'] = group_name
    context['at_group_id'] = at_group['group']['id']


def assert_at_group_exists_in_inventory(group_id: str):
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('group')
        pk = group_id
        find_group = res.get(pk=pk)
        assert find_group['id'] == pk, \
            f'Group with id: {pk} not found in Ansible Tower. Response from server: {find_group}.'


def create_at_credential(context: dict, os: str):
    at_server_id = context['at_server_id']
    credentials_name = context['credentials_name']
    os = 1 if os == 'linux' else 2
    credentials = IMPL.ansible_tower.create_credentials(os, credentials_name, at_server_id)
    publickey = credentials['machineCredentials']['publicKey'] if os == 1 else None
    pk = credentials['machineCredentials']['id']
    inventory_id = context['at_inventory_id']
    bootstrap_configurations = IMPL.ansible_tower.add_bootstrap_configurations(
        os, pk, credentials_name,
        at_server_id, publickey,
        inventory_id, context['at_group_id'],
        context['at_group_type'], context['at_group_name'])
    assert bootstrap_configurations['success'], f'The credentials: {credentials_name} have not been saved!'
    configuration_id = bootstrap_configurations['bootstrapconfig']['machineCredentials'][0]['configurationId']
    context['at_configuration_id'] = configuration_id
    context[f'at_cred_primary_key_{credentials_name}'] = pk


def assert_credential_exists_on_at_server(credentials_name: str, key: str):
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('credential')
        cred_list = res.list(all_pages=True)
        assert any(credentials_name in c['name'] and c['id'] == key for c in cred_list['results']), \
            f'Credential: {credentials_name} with id: {key} not found in Ansible Tower server.'


def set_at_job_template_id(context: dict, job_template_name: str):
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('job_template')
        job_template_info = res.get(name=job_template_name)
        assert job_template_name in job_template_info['name'], \
            f'Job template {job_template_name}: not found in Ansible Tower.\nResponse from server: {job_template_info}.'
        context['job_template_id'] = job_template_info['id']


def assert_hostname_exists_on_at_server(server: api.Server, negation: bool=False):
    """
    You can search server name by: Public IP or Private IP or Hostname.
    Check what value is in defaults!
    """
    hostname = server.public_ip
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('host')
        hosts_list = res.list(group=None, host_filter=None)
        for m in hosts_list['results']:
            if negation:
                if hostname not in m['name']:
                    break
                raise AssertionError(
                    f'Hostname: {hostname} was not removed from Ansible Tower server.')
            elif hostname in m['name']:
                break
        else:
            if len(hosts_list['results']) == 10:
                raise AssertionError(
                    f"License count of 10 instances has been reached. Number of hosts: {len(hosts_list['results'])}.")
            raise AssertionError(
                f'Hostname: {hostname} not found in Ansible Tower server.')


def assert_at_user_on_server(cloud: Cloud, server: api.Server, expected_user: str):
    node = cloud.get_node(server)
    cmd = 'net user' if CONF.feature.dist.is_windows else 'cut -d : -f 1 /etc/passwd'
    with node.remote_connection() as conn:
        user_list = conn.run(cmd).std_out.split()
        assert expected_user in user_list, \
            f'User {expected_user} was not found on the server! User list output: {user_list}'


def launch_ansible_tower_job(context: dict, job_name: str, job_result: str):
    inventory_id = context['at_inventory_id']
    credentials_name = context['credentials_name']
    pk = context[f'at_cred_primary_key_{credentials_name}']
    at_python_path = ''
    if not CONF.feature.dist.is_windows:
        at_python_path = context['at_python_path']
    with at_settings.runtime_values(**AT_CONFIG):
        res = at_get_resource('job')
        job_settings = {
            "credential_id": pk,
            "extra_credentials": [],
            "extra_vars": [at_python_path],
            "inventory": inventory_id
        }
        my_job = res.launch(job_template=job_name,
                            monitor=False,
                            wait=True,
                            timeout=None,
                            no_input=True,
                            **job_settings)
        for _ in range(10):
            job_info = res.get(pk=my_job['id'])
            if job_info['status'] not in ['waiting', 'running', 'pending']:
                break
            time.sleep(5)
        else:
            raise AssertionError(f"Job #{my_job['id']} has not finished in 50s")
        assert job_info['status'] == job_result, (my_job['id'], job_info['status'])


def assert_deployment_work(cloud: Cloud, server: api.Server, expected_output: str):
    node = cloud.get_node(server)
    cmd = 'dir /B C:\scalr-ansible' if CONF.feature.dist.is_windows else 'ls /home/scalr-ansible/'
    with node.remote_connection() as conn:
        actual_output = conn.run(cmd).std_out.split()
        assert expected_output in actual_output, f'Deployment does not work! Output: {actual_output}'


def assert_param_exists_in_config(node: ExtendedNode, param_name: str, param_value: str, config_name: str = None):
    config_name = config_name or "/etc/chef/client.rb"
    with node.remote_connection() as conn:
        cmd = f"cat {config_name}"
        config_data = conn.run(cmd).std_out
        config_pams = dict(
            line.split() for line in filter(None, config_data.splitlines())
        )
        assert config_pams.get(param_name) == param_value

