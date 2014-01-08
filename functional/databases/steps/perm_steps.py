import time

from lettuce import world, step

from revizor2.fixtures import resources
from revizor2.cloud import Cloud
import logging


LOG = logging.getLogger('permissions')

@step('Then I install ([\w]+) client to ([\w\d]+)')
def prepare_environment(step, env, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Upload database test script')
    node.put(path='/root/check_db.py',
                    content=resources('scripts/check_db.py').get())
    LOG.info('Launch database test script for update environment')
    node.run('python /root/check_db.py --db=%s' % env)


@step('And I can connect to ([\w]+) from ([\w\d]+) to ([\w\d]+)')
def assert_check_connect(step, db_type, from_serv, to_serv):
    time.sleep(120)
    from_server = getattr(world, from_serv)
    to_server = getattr(world, to_serv)
    node = world.cloud.get_node(from_server)
    password = world.farm.db_info('postgresql')['password']
    LOG.info('Run database test script with parameters: db=%s password=%s dest=%s' % (db_type, password, to_server.private_ip))
    out = node.run('python /root/check_db.py --db=%s --user=scalr --password=%s --to=%s' % (db_type, password, to_server.private_ip))
    if out[2]:
        raise AssertionError("Can't connect from %s to %s, stdout:%s stderr:%s exitcode:%s" %
                             (from_server.private_ip, to_server.private_ip, out[0], out[1], out[2]))
