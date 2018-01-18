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
    #TODO: Add systemd support
    server = getattr(world, serv_as)
    LOG.debug('Want check process %s and options %s' % (process, options))
    node = world.cloud.get_node(server)
    for attempt in range(3):
        out = node.run('ps aux | grep %s' % process)
        LOG.debug('Grep for ps aux: %s' % out[0])
        for line in out[0].splitlines():
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
    server = getattr(world, serv_as)
    if CONF.feature.dist.is_windows:
        node_name = world.run_cmd_command(server, 'findstr node_name c:\chef\client.rb').std_out
    else:
        node = world.cloud.get_node(server)
        node_name = node.run('cat /etc/chef/client.rb | grep node_name')[0]
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

    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)


    # Get chef client.pem update time
    bootstrap_stat = node.run('stat -c %Y /etc/chef/client.pem')[0].split()[0]
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
    stdout, stderr, exit = node.run("systemctl status chef-client")
    assert exit == 0, 'chef-client ended with exit code: %s' % exit
    assert stderr == '', 'Error on chef-client restarting: %s' % stderr
    assert 'chef-client -i {}'.format(interval) in stdout


@step('I wait and see that chef-client runs more than INTERVAL (\d+) on (\w+)')
def chef_runs_time(step, interval, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    intervalx3 = int(interval) * 3
    time.sleep(intervalx3)
    stdout, stderr, exit = node.run("systemctl status chef-client")
    active_line = stdout.splitlines()[2]
    match = re.search('(?:(\d+)min)? (\d+)s', active_line)
    minutes = match.group(1)
    seconds = int(match.group(2))
    runtime = (int(minutes) * 60) + seconds if minutes else seconds
    assert int(runtime) > intervalx3


@step('Initialization was failed on "([a-zA-Z]+)" phase with "([\w\W]+)" message on (\w+)')
def check_failed_status_message(step, phase, msg, serv_as):
    server = getattr(world, serv_as)
    patterns = (phase, msg)
    failed_status_msg = server.get_failed_status_message()
    msg_head = failed_status_msg.split("\n")[0].replace("&quot;", "")
    LOG.debug('Initialization status message: %s' % msg_head)
    assert all(pattern in msg_head for pattern in patterns), \
        "Initialization was not failed on %s with message %s" % patterns


@step("I add a new link with os '([\w-]+)' and Inventory '([\w-]+)' and create credentials '([\w-]+)' for server '([\w-]+)'")
def create_credential(step, os, inv_name, cred_name, serverId):
    data = IMPL.ansible_tower.create_credentials(os, cred_name, serverId)
    publicKey = None
    if os == "linux":
        publicKey = data['machineCredentials']['publicKey']
    pk = data['machineCredentials']['id']
    setattr(world, 'at_cred_primary_key_%s' % cred_name, pk)
    passw = data['machineCredentials']['password']
    save_at_cred = IMPL.ansible_tower.save_credentials(inv_name, os, pk, cred_name, serverId, publicKey, passw)
    if not save_at_cred['success']:
        raise AssertionError('The credentials: %s have not been saved!' % cred_name)


@step("credential '([\w-]+)' exists in ansible-tower credentials list")
def check_credential_exists_on_at_server(step, cred_name):
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('credential')
        pk = getattr(world, 'at_cred_primary_key_%s' % cred_name)
        cred_list = res.list(all_pages=True)
        for m in cred_list['results']:
            if cred_name in m['name'] and m['id'] == pk:
                # raise Exception(m['name'], m['id'])
                break
        else:
            raise AssertionError(
                'Credential name: %s not found in Ansible Tower server.' % cred_name)


@step("server ([\w\d]+) exists in ansible-tower hosts list")
def check_hostname_exists_on_at_server(step, serv_as):
    server = getattr(world, serv_as)
    hostname = world.get_hostname_by_server_format(server)
    with at_settings.runtime_values(**at_config):
        res = at_get_resource('host')
        hosts_list = res.list(group=None, host_filter=None)
        for m in hosts_list['results']:
            if hostname in m['name']:
                break
        else:
            if len(hosts_list['results']) >= 10:
                raise AssertionError(
                    'License count of 10 instances has been reached. Number of hosts: %s .' % (
                        len(hosts_list['results'])))
            raise AssertionError(
                'Hostname: %s not found in Ansible Tower server.' % hostname)
        # found


# @step("I launch job '([\w-]+)' with credential '([\w-]+)'")
# def launch_ansible_tower_job(step, job_name, at_user):
#     with at_settings.runtime_values(**at_config):
#         res = at_get_resource('job')
#         job_settings = {
#             "name": job_name,
#             "description": "",
#             "organization": 1,
#             "variables": ""}
#         res.launch( **job_settings)
#         job_list = res.list()
#         for m in job_list['results']:
#             if job_name in m['name']:
#                 break
#         else:
#             raise AssertionError(
#                 'Jod: %s not found in Ansible Tower server.' % job_name)


@after.each_feature
def delete_ansible_tower_credential(feature):
    provision_feature_list = [
        'Linux server provision with chef and ansible tower',
        'Windows server provision with chef and ansible tower'
    ]
    if feature.name in provision_feature_list:
        cred_name = 'Revizor_windows_cred' if CONF.feature.dist.is_windows else 'Revizor_linux_cred'
        with at_settings.runtime_values(**at_config):
            res = at_get_resource('credential')
            pk = getattr(world, 'at_cred_primary_key_%s' % cred_name)
            result = res.delete(pk=pk)
            assert result['changed'], (
                    'Credentials with name %s are not deleted from the AT server' % cred_name)
            LOG.error('Credentials: %s  with the id: %s were not removed from the AT server' % (
                cred_name, pk))
