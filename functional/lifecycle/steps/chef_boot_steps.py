import chef
import logging
import time

from revizor2.conf import CONF
from revizor2.consts import Platform, Dist
from lettuce import world, step


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


@step('I change chef-client INTERVAL to (\d+) sec on (\w+)')
def change_chef_interval(step, interval, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('echo -e "INTERVAL={%}" >> /etc/default/chef-client'.format(interval))


@step('Restart chef-client process on (\w+)')
def restart_chef_client(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if CONF.feature.dist.is_systemd:
        cmd = "systemctl restart chef-client"
    else:
        cmd = "/etc/etc/init.d/chef-client restart"
    node = world.cloud.get_node(server)
    node.run(cmd)
    LOG.info('chef-client restart complete')


@step('I verify that this value (\d+) appears in the startup line on (\w+)')
def verify_interval_value(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    INTERVAL=*
    assert 'INTERVAL=15' == node.run(
		'cat /opt/chef/embedded/bin/ruby --disable-gems /usr/bin/chef-client -i 15 -L /var/log/chef-client.log | grep INTERVAL')


@step('I wait and see that chef-client runs more than INTERVAL')
def chef_runs_time(step, interval, serv_as):
    time.sleep(interval * 3)
    response = node.run('systemctl list-units')
    services = response.split()
    #assert any(map(lambda service: 'chef-client' in s, services))
 	assert some_run_time > (interval * 3)



