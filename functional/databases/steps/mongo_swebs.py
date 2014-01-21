import time
import logging

from lettuce import world, step


LOG = logging.getLogger('mongodb')


@step('I create file in (.+)$')
def create_file(step, serv_as):
    time.sleep(120)
    db_role = world.get_role()
    if serv_as == 'master':
        server = db_role.db.get_master()
    else:
        server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('touch /mnt/mongodb-storage/master')


@step('start terminate cluster$')
def terminate_cluster(step):
    world.farm.mongodb_terminate()


@step('master have file$')
def assert_check_file(step):
    db_role = world.get_role()
    server = db_role.db.get_master()
    node = world.cloud.get_node(server)
    out = node.run('ls /mnt/mongodb-storage/master')
    world.assert_in('No such file or directory', out[0], 'Not see file in master ebs: %s' % out[0])
