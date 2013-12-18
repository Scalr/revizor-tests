import logging

from lettuce import world, step


LOG = logging.getLogger('chef')


@step("process '([\w-]+)' has options '(.+)' in (.+)")
def check_process_options(step, process, options, serv_as):
    server = getattr(world, serv_as)
    LOG.debug('Want check process %s and options %s' % (process, options))
    node = world.cloud.get_node(server)
    out = node.run('ps aux | grep %s' % process)
    LOG.debug('Grep for ps aux: %s' % out[0])
    for line in out[0].splitlines():
        if line.split()[10].startswith('grep'):
            continue
        LOG.info('Work with line: %s' % line)
        if not options in ' '.join(line.split()[10:]):
            raise AssertionError('Options %s not in process, %s' % (options, ' '.join(line.split()[10:])))
        else:
            return True
    raise AssertionError('Not found process: %s' % process)


@step("chef node_name in ([\w\d]+) set by global hostname")
def verify_chef_hostname(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node_name = node.run('cat /etc/chef/client.rb | grep node_name')[0].strip().split()[1][1:-1]
    hostname = node.run('hostname')[0].strip()
    if not node_name == hostname:
        raise AssertionError('Chef node_name %s != hostname on server %s' % (node_name, hostname))

