from lettuce import world, step
import logging

LOG = logging.getLogger(__name__)


@step('And ([^ .]+) is slave of ([^ .]+)')
def assert_check_slave(step, slave_serv, master_serv):
    slave_server = getattr(world, slave_serv)
    master_server = getattr(world, master_serv)
    db_role = world.get_role()
    slaves = db_role.db.get_slaves()
    master = db_role.db.get_master()
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
    node_result = world.cloud.get_node(server).run("find /mnt/redisstorage/ -name '%(search)s*'" % {'search': search})
    if search in node_result.std_out:
        raise AssertionError("Database dump file: %s, exists. Node run status is: %s. Search mask: %s" %
                             (node_result.std_out, node_result.status_code, search))


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
    # Setup attrs
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    service_paths= world.get_service_paths(process, node=node, service_conf='redis.6379.conf')
    LOG.info('Start %s on remote host: %s' % (process, server.public_ip))
    # Set run command
    cmd = "/bin/su redis -s /bin/bash -c \"%(bin)s %(conf)s\" " \
          "&& sleep 5 " \
          "&&  pgrep -l %(process)s | awk {print'$1'}" % ({
              'bin': service_paths.get('bin'),
              'process': process,
              'conf': service_paths.get('conf')})
    # Run command
    node_result = node.run(cmd)
    if node_result.status_code:
        raise AssertionError("Can't run %s. Error: %s %s" % (process, node_result.std_out, node_result.std_err))
    LOG.info('%s was successfully started on remote host: %s' % (process, server.public_ip))