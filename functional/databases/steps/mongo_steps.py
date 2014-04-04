import time
import sys
import logging

from lettuce import world, step
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.conf import CONF
from random import sample
from pymongo.errors import OperationFailure
from revizor2 import exceptions
from bson.objectid import ObjectId

LOG = logging.getLogger('mongodb')


@step('([\w]+) hostname is (.+)')
def assert_hostname(step, serv_as, hostname):
    server = getattr(world, serv_as)
    time.sleep(15)
    host = world.get_hostname(server)
    world.assert_not_equal(hostname.strip(), host.strip(), 'Hostname in %s is invalid. Must be %s, but %s' % (serv_as, hostname, host))


@step('And port ([\d]+) is( not | )listen in (.+)$')
def assert_port(step, port, state, serv_as):
    if serv_as == 'all':
        world.farm.servers.reload()
        servers = [s for s in world.farm.servers if s.status == 'Running']
    else:
        servers = [getattr(world, serv_as), ]
    state = state.strip()
    state = False if state == 'not' else True
    for serv in servers:
        time.sleep(60)
        if state:
            res = wait_until(world.check_open_port, args=(serv, port.strip()), timeout=600,
                             error_text="Port %s is not open" % port)
        else:
            res = world.check_open_port(serv, port.strip())
        world.assert_not_equal(state, res, 'Port %s is %s, but must %s in server %s' % (port, res, state, serv.id))


@step('And port ([\d]+) is listen only in (.+)$')
def listen_only(step, port, serv_as):
    world.farm.servers.reload()
    servers = [s for s in world.farm.servers if s.status == 'Running']
    server = getattr(world, serv_as)
    port = port.strip()
    wait_until(world.check_open_port, args=(server, port.strip()),
               timeout=600, error_text="Port %s is not open" % port)
    for serv in servers:
        if serv.id == server.id:
            continue
        time.sleep(60)
        res = world.check_open_port(serv, port.strip())
        world.assert_exist(res, 'Port %s is open, but must be closed in server %s' % (port, serv.id))


@step('I (add|delete) replicaset')
def replicaset_control(step, action):
    world.farm.mongodb_replicaset(action)
    time.sleep(60)


@step('([\w]+) is master$')
def check_master(step, serv_as):
    server = getattr(world, serv_as)
    db_role = world.get_role()
    credentials = {'ssl': CONF.feature.ssl_on}
    res = db_role.db.check_master(server, credentials=credentials)
    world.assert_not_exist(res, '%s is not master' % server.id)
    LOG.info('Master checked. %s is master. ' % serv_as)


@step('wait ([\w]+) (as replica )?have data in database ([\w]+)$')
def wait_data_in_mongodb(step, serv_as, replica, db_name):
    server = getattr(world, serv_as)
    db_role = world.get_role()
    credentials = {'ssl': CONF.feature.ssl_on}
    # Set credentials
    if replica:
        credentials.update({'replicaSet': serv_as, 'readPreference': 'secondary'})
    # Get connection
    connection = db_role.db.get_connection(server, credentials=credentials)
    LOG.info('Checking data on %s. Connected with %s options.' % (serv_as, credentials))
    # Get randomom collection
    id = dict(sample(world.data_insert_result.items(), 3))
    # Get document from random collection
    id = dict([(key, sample(value, 10)) for key, value in id.iteritems()])
    # Check inserted data in database
    LOG.info('Random data requested with a replica: ' % id)
    start_time = time.time()
    while (time.time() - start_time) <= 600:
        collection_count = len(id)
        for collection, objects in id.iteritems():
            try:
                LOG.info('Try to get documents: %s from random collection %s.' % (objects, collection))
                records_count = connection[db_name][collection].find({'_id': {'$in': objects}}).count()
                LOG.info('Obtained documents count from random collection %s:%s on %s.' % (collection, records_count, serv_as))
            except:
                raise OperationFailure('An error occurred while trying to get collection from %s database.\n'
                                       'Original error: %s' % (db_name, sys.exc_info()[1]))
            if not records_count:
                break
            if records_count != len(objects):
                raise AssertionError('An error occurred while trying to check data.\n'
                                     'Server %s has not data from %s' % (serv_as, objects))
            collection_count -= 1
        if not collection_count:
            break
        time.sleep(5)
    else:
        raise exceptions.TimeoutError('Timeout: 600 seconds reached.\n'
                                      'Server %s has not all inserted data to %s database.' % (server, db_name))
    LOG.info('Random data checked successfully on %s' % serv_as)


@step('replicaset status is valid on ([\w]+) port ([\d]+)$')
def check_status(step, serv_as, port):
    server = getattr(world, serv_as)
    db_role = world.get_role()
    # Set credentials
    credentials = {'ssl': CONF.feature.ssl_on, 'port': int(port)}
    # mongod replicaSet status command
    command = {'replSetGetStatus': 1}
    # Get status
    res = db_role.db.run_admin_command(server, command, credentials=credentials)
    master_name = [member['name'] for member in res['members'] if member['state'] == 1][0]
    LOG.info('Obtained replica set status from: %s\n%s' % (serv_as, res))
    # Check status
    for replica_member in res['members']:
        if replica_member.get('self', False):
            if (replica_member['state'] != 2) or (res.get('syncingTo', False) != master_name):
                raise AssertionError('An error occurred while trying to check data.\n'
                                     'ReplicaSet status in Error states: %s or not synced with master: %s.'
                                     % (replica_member['stateStr'], master_name))
            break
    else:
        raise AssertionError("An error occurred while trying to check data. Can't get replica member %s." % serv_as)
    LOG.info('ReplicaSet status checked successfully on %s' % serv_as)


@step('([\w]+) is(?: ([\w]+))? running on port ([\d]+) in shard S([\d]+)')
def check_state(step, states, revert, port, shard_index):
    member_states = {
        'STARTUP': 0,
        'PRIMARY': 1,
        'SECONDARY': 2,
        'RECOVERING': 3,
        'FATAL': 4,
        'STARTUP2': 5,
        'UNKNOWN': 6,
        'ARBITER': 7,
        'DOWN': 8,
        'ROLLBACK': 9,
        'SHUNNED': 10
    }
    world.farm.servers.reload()
    db_role = world.get_role()
    revert = True if revert else False
    state = member_states[states.upper()]
    shard_index = int(shard_index)-1
    # Set credentials
    credentials = {'ssl': CONF.feature.ssl_on, 'port': 27018, 'readPreference': 'nearest'}
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
        raise AssertionError('No found servers in shard: #%s' % shard_index)
    # Check state
    start_time = time.time()
    state_is_matched = False
    while (time.time() - start_time) <= 300:
        if not state_is_matched:
            res = db_role.db.run_admin_command(server, command, credentials=credentials)
            LOG.info('Obtained replica set status from: %s\n%s' % (server.id, res))
            for member in res['members']:
                if member.get('state', 100) == state \
                   and member.get('name', '').split(':')[-1] == port \
                   and int(member.get('health', 0)):
                    if revert:
                        raise AssertionError('Found server: %s with state: %s in shard: #%s' % (server.id, states.upper(), shard_index))
                    state_is_matched = True
                    break
            time.sleep(10)
        else:
            break
    else:
        if not revert:
            raise exceptions.TimeoutError('Timeout: 600 seconds reached. '
                                          'State %s is not checked in shard: #%s.' % (states.upper(), shard_index))
    LOG.info('Server %s state %s. Checked successfully' % (server.id, states.upper()))


@step('(\w+) log rotated on ([\w\d]+) and new created with ([\d]+) rights')
def is_log_rotated(step, service, serv_as, rights):
    server = getattr(world, serv_as)
    if world.is_log_rotate(server, service, rights):
        LOG.info('The %s log\'s are successfully rotated on the remote host %s' % (service, server.public_ip))