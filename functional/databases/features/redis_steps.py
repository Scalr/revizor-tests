from lettuce import world, step

import logging


LOG = logging.getLogger('redis')


@step('And ([^ .]+) is slave of ([^ .]+)')
def assert_check_slave(step, slave_serv, master_serv):
    slave_server = getattr(world, slave_serv)
    master_server = getattr(world, master_serv)
    slaves = world.db.get_slaves()
    master = world.db.get_master()
    for s in slaves:
        if slave_server.id == s.id:
            if master_server.id == master.id:
                return True
            else:
                raise AssertionError("Server %s is not master" % master.id)
    raise AssertionError("Server %s is not slave" % slave_server.id)


@step("And I can't see databases ([\w]+) on ([\w]+)")
def assert_check_dumps(step, search, serv_as):
    """Search redis-server  dump file dump.*.rdb in the /mnt/redisstorage/dump.*.rdb"""
    server = getattr(world, serv_as)
    LOG.info('Search redis-server dump file dump.*.rdb in the /mnt/redisstorage/')
    node_result = world.cloud.get_node(server).run("find /mnt/redisstorage/ -name '%(search)s*'" % vars())
    if search in node_result[0]:
        raise AssertionError("Database dump file: %s, exists. Node run status is: %s. Search mask: %s" %
                             (node_result[0], node_result[2], search))


@step('Then I kill (.+) on ([\w]+)')
def kill_process(step, process, serv_as):
    """Kill redis-server  process"""
    server = getattr(world, serv_as)
    node_result = world.kill_process_by_name(server, process)
    if node_result:
        raise AssertionError('Process name:%s, pid:%s  was not properly killed on remote host %s'
                             % (process, node_result, server.public_ip))


@step('Then I start (.+) on ([\w]+)')
def start_redis_process(step, process, serv_as):
    """Start redis-server  process"""
    server = getattr(world, serv_as)
    LOG.info('Start %(process)s on remote host: %s' % (server.public_ip, vars()))
    node_result = world.cloud.get_node(server).run("/bin/su redis -s /bin/bash -c \"/usr/bin/%(process)s /etc/redis/redis.6379.conf\" && sleep 5 &&  pgrep -l %(process)s | awk {print'$1'}" % vars())
    if not node_result[0]:
        raise AssertionError("%(process)s was not properly started on remote host %s. Error is: %s "
                             % (vars(), server.public_ip, node_result[1]))





