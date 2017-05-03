import chef
import logging
import time
import re

from revizor2.conf import CONF
from revizor2.consts import Platform, Dist
from lettuce import world, step, before


LOG = logging.getLogger('chef')


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
    node = world.cloud.get_node(server)
    node_name = node.run('cat /etc/chef/client.rb | grep node_name')[0].strip().split()[1][1:-1]
    #hostname = world.get_hostname(server)
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
    if not CONF.feature.dist.is_systemd:
        scenario = [s for s in feature.scenarios if s.name == "Checking changes INTERVAL config"]
        if scenario:
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
