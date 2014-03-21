import time
import sys
import logging

from lettuce import world, step
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.conf import CONF
from random import randrange
from pymongo.errors import OperationFailure
from revizor2 import exceptions

LOG = logging.getLogger('mongodb')



@step('([\w]+) hostname is (.+)')
def assert_hostname(step, serv_as, hostname):
    serv = getattr(world, serv_as)
    time.sleep(15)
    host = world.get_hostname(serv)
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
    wait_until(world.check_open_port, args=(server, port.strip()), timeout=600, error_text="Port %s is not open" %
                                                                                           port)
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
    res = db_role.db.check_master(server, credentials={'ssl': CONF.feature.ssl_on})
    world.assert_not_exist(res, '%s is not master' % server.id)


@step('wait ([\w]+) have database ([\w]+) data$')
def check_data(step, serv_as, db_name):
    server = getattr(world, serv_as)
    db_role = world.get_role()
    id = {}
    options = {'ssl': CONF.feature.ssl_on}
    connection = db_role.db.get_connection(server, credentials=options)
    for i in xrange(3):
        coll_name = 'revizor[%s]' % randrange(0, 10, 1)
        id.update({coll_name: []})
        collection = False
        start_time = time.time()
        while not collection:
            try:
                collection = connection[db_name][coll_name].find()
            except:
                raise OperationFailure('An error occurred while trying to get collection from %s database.\n'
                                       'Original error: %s' % ('revizor-test', sys.exc_info()[1]))
            if (time.time() - start_time) >= 600:
                raise exceptions.TimeoutError('Timeout: 600 seconds reached.\n'
                                              'Server %s not have data on %s database.' % (server, db_name))
        for j in xrange(10):
            id[coll_name].append(collection[randrange(0, 100, 1)]['_id'])
    for key, value in id.iteritems():
        if any(id_obj not in world.data_id[key] for id_obj in value):
            raise AssertionError('An error occurred while trying to check data.\nServer %s not have data: %s' % serv_as)

@step('(\w+) log rotated on ([\w\d]+) and new created with ([\d]+) rights')
def is_log_rotated(step, service, serv_as, rights):
    server = getattr(world, serv_as)
    if world.is_log_rotate(server, service, rights):
        LOG.info('The %s log\'s are successfully rotated on the remote host %s' % (service, server.public_ip))