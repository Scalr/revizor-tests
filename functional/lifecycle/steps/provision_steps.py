import logging
import time
import re

import chef
from tower_cli import get_resource as at_get_resource
from tower_cli.conf import settings as at_settings

from revizor2.conf import CONF
from revizor2.consts import Platform, Dist
from revizor2.backend import IMPL
from lettuce import world, step, before, after


LOG = logging.getLogger('chef')
at_config = CONF.credentials.ansible_tower

@step("process '([\w-]+)' has options '(.+)' in (.+)")
def check_process_options(step, process, options, serv_as):
    # NOTE: migrated
    #TODO: Add systemd support
    server = getattr(world, serv_as)
    LOG.debug('Want check process %s and options %s' % (process, options))
    node = world.cloud.get_node(server)
    with node.remote_connection() as conn:
        for _ in range(3):
            out = conn.run('ps aux | grep %s' % process)
            LOG.debug('Grep for ps aux: %s' % out.std_out)
            for line in out.std_out.splitlines():
                if 'grep' in line:
                    continue
                LOG.info('Work with line: %s' % line)
                if options not in line and not CONF.feature.dist == Dist('amzn1609') and not CONF.feature.dist.is_systemd:
                    raise AssertionError('Options %s not in process, %s' % (options, ' '.join(line.split()[10:])))
                else:
                    return True
        raise AssertionError('Not found process: %s' % process)


@step("chef node_name in ([\w\d]+) set by global hostname")
def verify_chef_hostname(step, serv_as):
    # NOTE: migrated
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    cmd = 'findstr node_name c:\chef\client.rb' if CONF.feature.dist.is_windows else 'cat /etc/chef/client.rb | grep node_name'
    node_name = node.run(cmd).std_out
    node_name = node_name.strip().split()[1][1:-1]
    hostname = world.get_hostname_by_server_format(server)
    if not node_name == hostname:
        raise AssertionError('Chef node_name "%s" != hostname on server "%s"' % (node_name, hostname))


@step('chef log in ([\w\d]+) contains "(.+)"')
def verify_chef_log(step, serv_as, text):
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        if log.name == '[Scalr built-in] Chef bootstrap':
            if not text in log.message:
                raise AssertionError('Text "%s" not found in chef bootstrap:\n%s' % (text, log.message))
            return


@step("I ([\w\d]+) chef bootstrap stats on ([\w\d]+)")
def step_impl(step, action, serv_as):
    # NOTE: migrated
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)


    # Get chef client.pem update time
    bootstrap_stat = node.run('stat -c %Y /etc/chef/client.pem').std_out.split()[0]
    LOG.debug('Chef client.pem, last modification time: %s' % bootstrap_stat)

    if action == 'save':
        LOG.debug('Save chef client.pem, last modification time: %s' % bootstrap_stat)
        setattr(world, '%s_bootstrap_stat' % server.id, bootstrap_stat)
        return
    #
    saved_bootstrap_stat = getattr(world, '%s_bootstrap_stat' % server.id)
    assertion_msg = 'Chef client.pem, was modified after resume.'

    assert bootstrap_stat == saved_bootstrap_stat, assertion_msg


@step(r'server ([\w\d]+) ([\w]+\s)*exists on chef nodes list')
@world.run_only_if(dist=['!coreos'])
def check_node_exists_on_chef_server(step, serv_as, negation):
    server = getattr(world, serv_as)
    try:
         host_name = getattr(world, '%s_chef_node_name' % server.id)
    except AttributeError:
        host_name = world.get_hostname_by_server_format(server)
        setattr(world, '%s_chef_node_name' % server.id, host_name)
    LOG.debug('Chef node name: %s' % host_name)

    chef_api = chef.autoconfigure()
    LOG.debug('Chef api instance: %s' % chef_api)
    if not isinstance(chef_api, chef.api.ChefAPI):
        raise AssertionError("Can't initialize ChefAPI instance.")

    node = chef.Node(host_name, api=chef_api)
    node_exists = node.exists
    assert not node_exists if negation else node_exists, 'Node %s not in valid state on Chef server' % host_name


@before.each_feature
def exclude_scenario_without_systemd(feature):
    if not CONF.feature.dist.is_systemd and feature.name == 'Linux server provision with chef and ansible tower':
        scenario = [s for s in feature.scenarios if s.name == "Checking changes INTERVAL config"][0]
        feature.scenarios.remove(scenario)
        LOG.info('Remove "%s" scenario from test suite "%s" if feature.dist is not systemd' % (
            scenario.name, feature.name))


@step('I change chef-client INTERVAL to (\d+) sec on (\w+)')
def change_chef_interval(step, interval, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('echo -e "INTERVAL={}" >> /etc/default/chef-client'.format(interval))


@step('restart chef-client process on (\w+)')
def restart_chef_client(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run("systemctl restart chef-client")


@step('I verify that this INTERVAL (\d+) appears in the startup line on (\w+)')
def verify_interval_value(step, interval, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    out = node.run("systemctl status chef-client")
    assert out.status_code == 0, 'chef-client ended with exit code: %s' % out.status_code
    assert out.std_err == '', 'Error on chef-client restarting: %s' % out.std_err
    assert 'chef-client -i {}'.format(interval) in out.std_out


@step('I wait and see that chef-client runs more than INTERVAL (\d+) on (\w+)')
def chef_runs_time(step, interval, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    intervalx3 = int(interval) * 3
    time.sleep(intervalx3)
    out = node.run("systemctl status chef-client")
    active_line = out.std_out.splitlines()[2]
    match = re.search('(?:(\d+)min)? (\d+)s', active_line)
    minutes = match.group(1)
    seconds = int(match.group(2))
    runtime = (int(minutes) * 60) + seconds if minutes else seconds
    assert int(runtime) > intervalx3


@step("I set hostname '(.+)' that will be configured via the cookbook")
def save_chef_cookbook_hostname(step, chef_host_name):
    setattr(world, 'chef_hostname_for_cookbook', chef_host_name)
    LOG.debug('Chef hostname for cookbook: %s' % chef_host_name)


@step("server hostname in ([\w\d]+) is the same '(.+)'")
def verify_chef_cookbook_hostname(step, serv_as, chef_hostname):
    server = getattr(world, serv_as)
    server.reload()
    if not server.hostname == chef_hostname:
        raise AssertionError(
            'Hostname on server "%s" != chef hostname configured via the cookbook "%s"' % (
                server.hostname, chef_hostname))


@step("I get Ansible Tower server id")
def get_at_server_id(step):
    at_servers_list = IMPL.ansible_tower.list_servers()
    at_server_id = at_servers_list['servers'][0]['id']
    assert at_server_id, 'The Ansible-Tower server Id was not found'
    setattr(world, 'at_server_id', at_server_id)


@step("I create a copy of the inventory '([\w-]+)'")
def create_copy_at_inventory(step, inv_name):
    """
    I create a copy of the inventory for each run of the test.
    This is required to parallel the execution of jobs in running tests.
    """
    inventory_id = re.search('(\d.*)', inv_name).group(0)
    new_name = CONF.feature.dist.id + time.strftime("-%H:%M:%S:%MS")
    kwargs = {'description': new_name}
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('inventory')
        create_copy = res.copy(pk=inventory_id, new_name=new_name, **kwargs)
        setattr(world, 'at_inventory_id', create_copy['id'])
        setattr(world, 'at_inventory_name', create_copy['name'])
        if not new_name in create_copy['description']:
            raise AssertionError(
                'Inventory was not found in Ansible Tower. Response from server: %s.' % (
                    create_copy))


@step("I create a New AT '([\w-]+)' group '([\w-]+)'")
def create_at_group(step, group_type, group_name):
    """
    :param group_type: You can set 'regular' or 'template' type.
    """
    at_server_id = getattr(world, 'at_server_id')
    inventory_id = getattr(world, 'at_inventory_id')
    group_name = group_name + time.strftime("-%a-%d-%b-%Y-%H:%M:%S:%MS")
    at_group = IMPL.ansible_tower.create_inventory_groups(
        group_name, group_type, at_server_id, inventory_id)
    at_group_id = at_group['group']['id']
    setattr(world, 'at_group_name', group_name)
    setattr(world, 'at_group_id', at_group_id)
    setattr(world, 'at_group_type', group_type)


@step("AT group '([\w-]+)' exists in inventory in AT server")
def check_at_group_exists_in_inventory(step, group_name):
    group_name = getattr(world, 'at_group_name')
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('group')
        pk = getattr(world, 'at_group_id')
        find_group = res.get(pk=pk)
        if not group_name and pk in find_group:
            raise AssertionError(
                'Group: %s with id: %s not found in Ansible Tower. Response from server: %s.' % (
                    group_name, pk, find_group))


@step("I add a new link with os '([\w-]+)' and create credentials '([\w-]+)'")
def create_credential(step, os, credentials_name):
    at_server_id = getattr(world, 'at_server_id')
    os = 1 if os == 'linux' else 2
    credentials = IMPL.ansible_tower.create_credentials(os, credentials_name, at_server_id)

    publickey = None
    if os == 1: # "linux"
        publickey = credentials['machineCredentials']['publicKey']
    pk = credentials['machineCredentials']['id']
    inventory_id = getattr(world, 'at_inventory_id')
    setattr(world, 'at_cred_primary_key_%s' % credentials_name, pk)
    at_group_id = getattr(world, 'at_group_id')
    at_group_type = getattr(world, 'at_group_type')
    group_name = getattr(world, 'at_group_name')

    bootstrap_configurations = IMPL.ansible_tower.add_bootstrap_configurations(
        os, pk, credentials_name, at_server_id, publickey, inventory_id, at_group_id, at_group_type, group_name)
    if not bootstrap_configurations['success']:
        raise AssertionError('The credentials: %s have not been saved!' % credentials_name)
    configuration_id = bootstrap_configurations['bootstrapconfig']['machineCredentials'][0]['configurationId']
    setattr(world, 'configuration_id', configuration_id)
    setattr(world, 'credentials_name', credentials_name)

@step("credential '([\w-]+)' exists in ansible-tower credentials list")
def check_credential_exists_on_at_server(step, credentials_name):
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('credential')
        pk = getattr(world, 'at_cred_primary_key_%s' % credentials_name)
        cred_list = res.list(all_pages=True)
        for m in cred_list['results']:
            if credentials_name in m['name'] and m['id'] == pk:
                break
        else:
            raise AssertionError(
                'Credential: %s with id: %s not found in Ansible Tower server.' % credentials_name, pk)


@step("I get and save AT job template id for '([\w-]+)'")
def get_at_job_template_id(step, job_template_name):
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('job_template')
        job_template_info = res.get(name=job_template_name)
        if not job_template_name in job_template_info['name']:
            raise AssertionError(
                'Job template with name: %s not found in Ansible Tower. Response from server: %s.' % (
                    job_template_name, job_template_info))
        setattr(world, 'job_template_id', job_template_info['id'])


@step("I check dist and set ansible python interpreter as extra var for AT jobs")
def set_ansible_py_interpreter(step):
    at_python_path = 'at_python_path: null'
    if CONF.feature.dist.id in ['ubuntu-16-04', 'ubuntu-18-04']:
        at_python_path = 'at_python_path: 3'
    setattr(world, 'at_python_path', at_python_path)


@step(r"server ([\w\d]+) ([\w]+\s)*exists in ansible-tower hosts list")
def check_hostname_exists_on_at_server(step, serv_as, negation):
    """
    You can search server name by: Public IP or Private IP or Hostname.
    Check what value is in defaults!
    If value is Hostname, then hostname = world.get_hostname_by_server_format(server)
    """
    server = getattr(world, serv_as)
    hostname = server.public_ip
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('host')
        hosts_list = res.list(group=None, host_filter=None)
        for m in hosts_list['results']:
            if negation:
                if hostname not in m['name']:
                    break
                raise AssertionError(
                    'Hostname: %s was not removed from Ansible Tower server.' % hostname)
            elif hostname in m['name']:
                break
        else:
            if len(hosts_list['results']) == 10:
                raise AssertionError(
                    'License count of 10 instances has been reached. Number of hosts: %s .' % (
                        len(hosts_list['results'])))
            raise AssertionError(
                'Hostname: %s not found in Ansible Tower server.' % hostname)
        # found


@step("user '([\w-]+)' has been created in ([\w\d]+)")
def check_at_user_on_server(step, expected_user, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    cmd = 'net user' if CONF.feature.dist.is_windows else 'cut -d : -f 1 /etc/passwd'
    user_list = node.run(cmd).std_out.split()
    if not expected_user in user_list:
        raise AssertionError('User %s was not found on the server! User list output: %s' % (expected_user, user_list))


@step("I launch job '(.+)' with credential '([\w-]+)' and expected result '([\w-]+)' in (.+)")
def launch_ansible_tower_job(step, job_name, credentials_name, job_result, serv_as):
    inventory_id = getattr(world, 'at_inventory_id')

    pk = getattr(world, 'at_cred_primary_key_%s' % credentials_name)
    at_python_path = ''
    if not CONF.feature.dist.is_windows:
        at_python_path = getattr(world, 'at_python_path')
    with at_settings.runtime_values(**at_config):
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
            raise AssertionError('Job #%s has not finished in 50s' % my_job['id'])
        assert job_info['status'] == job_result, (my_job['id'], job_info['status'])


@step("I checked that deployment through AT was performed in (.+) and the output is '([\w-]+)'")
def check_deployment_work(step, serv_as, expected_output):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    cmd = 'dir /B C:\scalr-ansible' if CONF.feature.dist.is_windows else 'ls /home/scalr-ansible/'
    actual_output = node.run(cmd).std_out.split()
    if not expected_output in actual_output:
        raise AssertionError('Deployment does not work! Output: %s' % actual_output)


@after.each_feature
def delete_ansible_tower_group_credential(feature):
    """
    Cleaning on the AT server after passing tests.
    Removal: group, credential, inventory.
    """
    provision_feature_list = [
        'Linux server provision with chef and ansible tower',
        'Windows server provision with chef and ansible tower'
    ]
    if feature.name in provision_feature_list:
        credentials_name = 'Revizor-windows-cred' if CONF.feature.dist.is_windows else 'Revizor-linux-cred'
        with at_settings.runtime_values(**at_config):
            res = at_get_resource('credential')
            pk = getattr(world, 'at_cred_primary_key_%s' % credentials_name)
            result = res.delete(pk=pk)
            assert result['changed'], (
                    'Credentials with name %s are not deleted from the AT server' % credentials_name)
            LOG.error('Credentials: %s  with the id: %s were not removed from the AT server' % (
                credentials_name, pk))
            res = at_get_resource('group')
            at_group_id = getattr(world, 'at_group_id')
            result = res.delete(pk=at_group_id)
            assert result['changed'], ('Group with id: %s is not deleted from the AT server' % at_group_id)
            LOG.error('Group with id: %s is not deleted from the AT server' % at_group_id)
            res = at_get_resource('inventory')
            inventory_id = getattr(world, 'at_inventory_id')
            result = res.delete(pk=inventory_id)
            assert result['changed'], ('Inventory with id: %s is not deleted from the AT server' % inventory_id)
            LOG.error('Inventory with id: %s is not deleted from the AT server' % inventory_id)
