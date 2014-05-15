import time
import logging
import random

from lettuce import world, step
from revizor2.utils import wait_until

LOG = logging.getLogger('mongoshards')


@step('I (add|delete) shard')
def add_shard(step, action):
    world.farm.mongodb_shard(action)
    LOG.info('Add shard in farm %s' % world.farm.id)
    time.sleep(60)


@step('wait ([\d]+) servers is running')
def assert_wait_servers(step, serv_count):
    role = world.get_role()
    serv_count = int(serv_count)
    timeout = 60 * 15 * serv_count
    LOG.info('Wait %s servers, timeout %s seconds' % (serv_count, timeout))
    wait_until(world.wait_servers_running, args=(role, serv_count), timeout=timeout,
               error_text='Not see %s servers running' % serv_count)


@step('servers \[([\w\d,-]+)\] in replicaset R([\d]+) on port ([\d]+)$')
def assert_check_replicaset(step, slaves, shard_index, port):
    world.farm.servers.reload()
    db_role = world.get_role()
    shard_index = int(shard_index) - 1
    # Set credentials
    credentials = {'port': int(port), 'readPreference': 'secondary'}
    # mongod replicaSet status command
    command = {'replSetGetStatus': 1}
    # Get random server from shard
    for server in world.farm.servers:
        if server.status == 'Running' and server.role_id == db_role.role_id:
            if int(server.cluster_position[0]) == shard_index:
                server = server
                LOG.info('Found server %s with cluster position %s' % (server.id, server.cluster_position))
                break
    else:
        raise AssertionError('No servers found in shard: #%s' % shard_index)
    shard_members = slaves.split(',')
    # Run command
    res = db_role.db.run_admin_command(server, command, credentials=credentials)
    LOG.info('Obtained replica set status from: %s\n%s' % (server.id, res))
    # Check result
    members = set([member['name'].split('mongo')[1].split(':')[0][1:] for member in res['members']])
    LOG.info('Members in replicaSet %s are %s' % (shard_index, ','.join(members)))
    for shard_member in shard_members:
        world.assert_not_in(shard_member, members, 'Member %s not in replicaset. Members: %s' % (shard_member, members))


@step('cluster map has ([\d]+) shards')
def assert_shard_status(step, serv_count):
    serv_count = int(serv_count)
    db_role = world.get_role()
    world.farm.servers.reload()
    # mongod Shard list command
    command = {'listShards': 1}
    # Set credentials
    credentials = {'port': 27017, 'readPreference': 'primary'}
    # Get random server from shard
    for server in world.farm.servers:
        if server.status == 'Running' and server.role_id == db_role.role_id:
            if server.cluster_position == '0-0':
                server = server
                LOG.info('Found server %s with cluster position %s' % (server.id, server.cluster_position))
                break
    else:
        raise AssertionError('No servers found with index 0-0')
    # Run command
    res = db_role.db.run_admin_command(server, command, credentials=credentials)
    LOG.info('Obtained Shards list from: %s\n%s' % (server.id, res))
    # Check result
    world.assert_not_equal(serv_count, len(res['shards']), 'Cluster map has not %s shards. Found %s shard' % (len(res['shards']), serv_count))
    LOG.info('Cluster map has %s shards. Checked successfully.' % len(res['shards']))



@step('I random terminate ([\d]+) servers')
def random_terminates(step, serv_count):
    dead_index = random.sample(range(9), 5)
    role = world.get_role()
    servs = []
    for serv in world.farm.servers:
        if serv.status == 'Running' and serv.role_id == role.role_id:
            servs.append(serv)
    for i in dead_index:
        LOG.info('Terminate server %s' % servs[i].id)
        servs[i].terminate(force=True)


@step('wait cluster status ([\w]+)')
def check_cluster_terminate(step, status):
    wait_until(world.check_mongo_status, args=(status,), timeout=1800,
               error_text='Mongodb cluster status not %s, is: %s' % (status, world.farm.db_info('mongodb')['status']))
