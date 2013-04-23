import os
import time
import socket
import urllib2
import logging
from datetime import datetime


from lettuce import world, step

from revizor2.api import IMPL
from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.dbmsr import Database
from revizor2.utils import wait_until
from revizor2.consts import Platform, ServerStatus

LOG = logging.getLogger('databases')

#TODO: add to all methods which call dbmsr 3 retries

PORTS_MAP = {'mysql': 3306, 'mysql2': 3306, 'percona':3306, 'postgresql': 5432, 'redis': 6379, 'mongodb': 27018,
             'mysqlproxy': 4040}

STORAGE_ENGINES_EC2 = {'eph': {'db.msr.data_storage.engine': 'eph',
                               'db.msr.data_storage.eph.disk': '/dev/sda2',
                               'aws.instance_type':'m1.small',
                               'aws.use_ebs': '0'},
                       'lvm': {'db.msr.data_storage.engine': 'lvm',
                               'aws.instance_type':'m1.small',
                               'db.msr.data_storage.fstype': 'ext3',
                               'db.msr.storage.lvm.volumes': '{"ephemeral0":"150"}',
                               'db.msr.data_storage.eph.disk': '/dev/sda2'},
                       'raid10': {'db.msr.data_storage.engine': 'raid.ebs',
                                  'db.msr.data_storage.raid.level': '10',
                                  'db.msr.data_storage.raid.volume_size': '1',
                                  'db.msr.data_storage.raid.volumes_count': '4'},
                       'raid5': {'db.msr.data_storage.engine': 'raid.ebs',
                                 'db.msr.data_storage.raid.level': '5',
                                 'db.msr.data_storage.raid.volume_size': '1',
                                 'db.msr.data_storage.raid.volumes_count': '3'},
                       'raid0': {'db.msr.data_storage.engine': 'raid.ebs',
                                 'db.msr.data_storage.raid.level': '0',
                                 'db.msr.data_storage.raid.volume_size': '1',
                                 'db.msr.data_storage.raid.volumes_count': '2'},
                       'raid1': {'db.msr.data_storage.engine': 'raid.ebs',
                                 'db.msr.data_storage.raid.level': '1',
                                 'db.msr.data_storage.raid.volume_size': '1',
                                 'db.msr.data_storage.raid.volumes_count': '2'},
                       'ebs': {'db.msr.data_storage.engine': 'ebs',
                               'db.msr.data_storage.ebs.size': '1'}
}


STORAGE_ENGINES_RSNG = {
    'cinder': {
        "db.msr.data_storage.engine": "cinder",
        "db.msr.data_storage.cinder.size": "100",
        "db.msr.data_storage.fstype": "ext3",
        },

    'lvm': {
        "db.msr.data_storage.engine": "lvm",
        "db.msr.data_storage.fstype": "ext3",
        "db.msr.data_storage.cinder.size": "1",
        },
    'eph': {
        "db.msr.data_storage.engine": "eph",
        "db.msr.data_storage.fstype": "ext3",
        "db.msr.data_storage.eph.disk": "/dev/loop0"
    }
}


STORAGE_ENGINES_GCE = {
    'persistent': {
        "db.msr.data_storage.engine": "gce_persistent",
        "db.msr.data_storage.gced.size": "1",
        "db.msr.data_storage.fstype": "ext3"
    },
    'lvm': {
        "db.msr.data_storage.engine": "lvm",
        "db.msr.data_storage.fstype": "ext3",
        "db.msr.data_storage.eph.disk": "ephemeral-disk-0",
        "db.msr.storage.lvm.volumes": "{\"google-ephemeral-disk-0\":420}"
    },
    'eph': {
        "db.msr.data_storage.engine": "eph",
        "db.msr.data_storage.eph.disk": "ephemeral-disk-0",
        "db.msr.data_storage.fstype": "ext3",
    }
}

@step(r'I add (.+) role to this farm(?: on (.+))?$')
def add_role_to_given_farm(step, role_type, storage=None):
    #TODO: Move all actions with set role attribute here
    LOG.info("Add %s role to farm" % role_type)
    if storage:
        engine = storage
    else:
        engine = CONF.main.storage
    LOG.info('Use storage engine: %s' % engine)
    world.role_type = role_type
    scripting = []
    if CONF.main.driver == Platform.EC2:
        options = STORAGE_ENGINES_EC2[engine]
    elif CONF.main.driver in [Platform.RACKSPACE_US, Platform.ENTERIT]:
        if not engine in STORAGE_ENGINES_RSNG:
            engine = 'cinder'
        options = STORAGE_ENGINES_RSNG[engine]
    elif CONF.main.driver == Platform.GCE:
        if not engine in STORAGE_ENGINES_GCE:
            engine = 'persistent'
        options = STORAGE_ENGINES_GCE[engine]
    else:
        options = {}
    if role_type == 'redis':
        options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),})
    options.update({'db.msr.data_bundle.use_slave': True})
    world.role_options = options
    world.role_scripting = scripting
    role = world.add_role_to_farm(world.role_type, options=options, scripting=scripting)
    setattr(world, world.role_type + '_role', role)
    LOG.info("Set DB object to world")
    if role_type in ['mysql', 'postgresql', 'redis', 'mongodb', 'percona', 'mysql2', 'percona2']:
        db = Database.create(role)
        if not db:
            raise AssertionError('Database for role %s not found!' % role)
        setattr(world, 'db', db)


@step(r'And ([\w]+) is running on (.+)')
def assert_check_service(step, service, serv_as):
    LOG.info("Check service %s" % service)
    server = getattr(world, serv_as)
    port = PORTS_MAP[service]
    cloud = Cloud()
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        node = cloud.get_node(server)
        new_port = cloud.open_port(node, port, ip=server.public_ip)
    else:
        new_port = port
    if world.role_type == 'redis':
        LOG.info('Role is redis, add iptables rule for me')
        node = cloud.get_node(server)
        my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
        LOG.info('My IP address: %s' % my_ip)
        node.run('iptables -I INPUT -p tcp -s %s --dport 6379:6395 -j ACCEPT' % my_ip)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    try:
        s.connect((server.public_ip, new_port))
    except (socket.error, socket.timeout), e:
        raise AssertionError(e)
    if service == 'redis':
        LOG.info('Set main redis instances to %s' % serv_as)
        setattr(world, 'redis_instances', {6379: world.farm.db_info('redis')['password']})
    LOG.info("Service work")


@step(r'I trigger ([\w]+) creation( on slave)?')
def trigger_creation(step, action, use_slave=None):
    #TODO: if databundle in progress, wait 10 minutes
    action = action.strip()
    use_slave = True if use_slave else False
    if action == 'databundle':
        t = 'Bundle'
    elif action == 'backup':
        t = 'Backup'
    info = world.farm.db_info(world.db.db_name)
    setattr(world, 'last_%s' % action, info['dtLast%s' % t])
    if action == 'databundle':
        getattr(world.farm, 'db_create_%s' % action)(world.db.db_name, use_slave=use_slave)
    else:
        getattr(world.farm, 'db_create_%s' % action)(world.db.db_name)
    LOG.info("I'm trigger %s" % action)
    time.sleep(180)


@step(r'Last (.+) date updated to current')
def assert_check_databundle_date(step, back_type):
    LOG.info("Check %s date" % back_type)
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        LOG.info('Platform is cloudstack-family, backup not doing')
        return True
    info = world.farm.db_info(world.db.db_name)
    t = 'Backup'
    if back_type == 'databundle':
        t = 'Bundle'
    elif back_type == 'backup':
        t = 'Backup'
    if not info['dtLast%s' % t] == getattr(world, 'last_%s' % back_type, 'Never'):
        return
    else:
        raise AssertionError('Previous data%s was: %s and last: %s' % (t, getattr(world, 'last_%s' % back_type, 'Never'), info['dtLast%s' % t]))


@step(r'I have small-sized database (.+) on ([\w]+)')
def having_small_database(step, db_name, serv_as):
    server = getattr(world, serv_as)
    LOG.info("Create database %s in %s" % (db_name, server.id))
    world.db.database_create(db_name, server)


@step(r'I create (\d+) databases on ([\w]+)$')
def create_many_databases(step, db_count, serv_as):
    server = getattr(world, serv_as)
    for c in range(int(db_count)):
        db_name = "MDB%s" % c
        LOG.info("Create database %s in %s" % (db_name, server.id))
        world.db.database_create(db_name, server)


@step('([^ .]+) is slave of ([^ .]+)$')
def assert_check_slave(step, slave_serv, master_serv):
    slave = getattr(world, slave_serv)
    master = getattr(world, master_serv)
    info = world.farm.db_info(world.db.db_name)
    try:
        if not info['master']['serverId'] == master.id:
            raise AssertionError('Master is not %s' % master_serv)
        for sl in info['slaves']:
            if sl['serverId'] == slave.id:
                return True
    except IndexError:
        raise AssertionError("I'm not see replication status")
    raise AssertionError('%s is not slave, all slaves: %s' % (slave_serv, info['slaves']))


@step('I create a ([\w]+)$')
def do_action(step, action):
    #TODO: Wait databundle will complete
    action = action.strip()
    getattr(world.farm, 'db_create_%s' % action)(world.db.db_name)
    LOG.info("Create %s" % action)


@step('I create a ([\w]+) databundle on ([\w]+)')
def create_databundle(step, bundle_type, when):
    LOG.info('Create a %s databundle on %s' % (bundle_type, when))
    if when == 'slave':
        use_slave = True
    else:
        use_slave = False
    world.farm.db_create_databundle(world.db.db_name, bundle_type, use_slave=use_slave)


@step('([\w]+) contains database (.+)$')
def check_database_in_new_server(step, serv_as, db_name):
    if serv_as == 'all':
        world.farm.servers.reload()
        servers = filter(lambda s: s.status == ServerStatus.RUNNING, world.farm.servers)
    else:
        servers = [getattr(world, serv_as),]
    for server in servers:
#               port = PORTS_MAP[world.db.db_name]
#               if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#                       cloud = Cloud()
#                       node = cloud.get_node(server)
#                       new_port = cloud.open_port(node, port, server.public_ip)
#               else:
#                       new_port = port
        world.assert_not_equal(world.db.database_exist(db_name, server), True, 'Database %s not exist in server %s, all db: %s' %
                                                                               (db_name, server.id, world.db.database_list(server)))
#               if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#                       cloud.close_port(node, new_port, server.public_ip)


@step('I create database (.+) on (.+)')
def create_new_database(step, db_name, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Create database %s in %s' % (db_name, server.id))
#       port = PORTS_MAP[world.db.db_name]
#       cloud = Cloud()
#       if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#               node = cloud.get_node(server)
#               new_port = cloud.open_port(node, port, server.public_ip)
#       else:
#               new_port = port
    world.db.database_create(db_name, server)
    LOG.info('Database was success create')
    time.sleep(60)
#       if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#               cloud.close_port(node, new_port, server.public_ip)


@step('And databundle type in ([\w\d]+) is ([\w]+)')
def check_bundle_type(step, serv_as, bundle_type):
    LOG.info('Check databundle type')
    time.sleep(10)
    server = getattr(world, serv_as)
    c = Cloud()
    node = c.get_node(server)
    out = node.run("cat /var/log/scalarizr_debug.log | grep 'name=\"DbMsr_CreateDataBundle\"'")
    bundle = out[0].split('<backup_type>')[1].split('</backup_type>')[0]
    LOG.info('Databundle type in server messages: %s' % bundle)
    if not bundle == bundle_type:
        raise AssertionError('Bundle type in scalarizr message is not %s it %s' % (bundle_type, bundle))


@step('I increase storage to ([\d]+) Gb in ([\w\d]+) role$')
def increase_storage(step, size, role_type):
    size = int(size)
    if role_type == 'percona2':
        role_type = 'percona'
    LOG.info('Increase storage for %s role to %s Gb' % (role_type, size))
    setattr(world, 'grow_old_size', int(round(world.farm.db_info(role_type)['storage']['size']['total'])))
    grow_id = world.farm.db_increase_storage(role_type, size)
    LOG.info('Grow proccess id is %s' % grow_id)
    setattr(world, 'grow_status_id', grow_id)
    setattr(world, 'grow_new_size', size)


@step('grow status is ([\w\d]+)$')
def check_grow_status(step, status):
    LOG.debug('Check grow status')
    wait_until(wait_grow_status, args=(status.strip(),), timeout=900, error_text='Not see grow status %s' % status)


def wait_grow_status(status):
    new_status = IMPL.services.grow_info(world.grow_status_id)['status']
    LOG.info('Grow status for id %s is %s' % (world.grow_status_id, new_status))
    if new_status == status:
        return True
    elif new_status in ['failed', 'error']:
        raise AssertionError('Status of growing is %s' % new_status)
    else:
        return False


@step('And new storage size is ([\d]+) Gb in ([\w\d]+) role')
def check_new_storage_size(step, size, role_type):
    size = int(size)
    if role_type == 'percona2':
        role_type = 'percona'
    new_size = int(round(world.farm.db_info(role_type)['storage']['size']['total']))
    LOG.info('New size is %s, must be: %s (old size: %s)' % (new_size, size, world.grow_old_size))
    if not new_size == size:
        raise AssertionError('New size is %s, but must be %s (old %s)' % (new_size, size, world.grow_old_size))
