import os
import time
import socket
import urllib2
import logging
from datetime import datetime, timedelta
import httplib

from lettuce import world, step
from lxml import html

from revizor2.api import IMPL
from revizor2.conf import CONF
from revizor2.dbmsr import Database
from revizor2.utils import wait_until
from revizor2.fixtures import resources
from revizor2.consts import Platform, ServerStatus

LOG = logging.getLogger('databases')

#TODO: add to all methods which call dbmsr 3 retries

PORTS_MAP = {'mysql': 3306, 'mysql2': 3306, 'mariadb': 3306, 'percona':3306, 'postgresql': 5432, 'redis': 6379,
             'mongodb': 27018, 'mysqlproxy': 4040}


# @step(r'([\w]+) is( not)? running on (.+)')
# def assert_check_service(step, service, has_not, serv_as):
#     LOG.info("Check service %s" % service)
#     server = getattr(world, serv_as)
#     has_not = has_not and True or False
#     port = PORTS_MAP[service]
#     if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#         node = world.cloud.get_node(server)
#         new_port = world.cloud.open_port(node, port, ip=server.public_ip)
#     else:
#         new_port = port
#     if world.role_type == 'redis':
#         LOG.info('Role is redis, add iptables rule for me')
#         node = world.cloud.get_node(server)
#         try:
#             my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
#         except httplib.BadStatusLine:
#             time.sleep(5)
#             my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
#         LOG.info('My IP address: %s, add rules' % my_ip)
#         node.run('iptables -I INPUT -p tcp -s %s --dport 6379:6394 -j ACCEPT' % my_ip)
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.settimeout(15)
#     try:
#         s.connect((server.public_ip, new_port))
#     except (socket.error, socket.timeout), e:
#         raise AssertionError(e)
#     if service == 'redis':
#         LOG.info('Set main redis instances to %s' % serv_as)
#         setattr(world, 'redis_instances', {6379: world.farm.db_info('redis')['access']['password'].split()[2][:-4]})
#     LOG.info("Service work")


@step(r'I trigger ([\w]+) creation( on slave)?')
def trigger_creation(step, action, use_slave=None):
    #TODO: if databundle in progress, wait 10 minutes
    action = action.strip()
    use_slave = True if use_slave else False
    info = world.farm.db_info(world.db.db_name)
    if action != 'pmaaccess':
        setattr(world, 'last_%s' % action, info['last_%s' % action])
    if action == 'databundle':
        getattr(world.farm, 'db_create_%s' % action)(world.db.db_name, use_slave=use_slave)
    else:
        getattr(world.farm, 'db_create_%s' % action)(world.db.db_name)
    LOG.info("I'm trigger %s" % action)
    time.sleep(180)

@step(r'I launch ([\w]+) session')
def launch_session(step, service):
    """Step calling the appropriate service method to run it"""
    service = service.strip()
    LOG.info("I'm launch %s session" % service)
    world.launch_request = getattr(world.farm, 'db_launch_%s_session' % service)()


@step(r'([\w]+) is available, I see the ([\w]+) in the ([\w]+)')
def session_is_available(step, service, search_string, element):
    """Step checks for a running service by searching on the corresponding page of the relevant elements.
       Takes a variable as argument world.launch_request out of step launch_session"""
    if not world.launch_request:
        raise Exception('The %s service page is not found') % service
    tree = html.fromstring(world.launch_request.text)
    if search_string in tree.xpath('//%s' % element)[0].text:
        LOG.info("The %s service is launched." % service)
    else:
        raise AssertionError("The %s service is not launched." % service)


@step(r'Last (.+) date updated to current')
def assert_check_databundle_date(step, back_type):
    LOG.info("Check %s date" % back_type)
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        LOG.info('Platform is cloudstack-family, backup not doing')
        return True
    info = world.farm.db_info(world.db.db_name)
    if not info['last_%s' % back_type] == getattr(world, 'last_%s' % back_type, 'Never'):
        return
    else:
        raise AssertionError('Previous %s was: %s and last: %s' % (back_type, getattr(world, 'last_%s' % back_type, 'Never'), info['last_%s' % back_type]))


@step(r'I have small-sized database (.+) on ([\w]+)')
def having_small_database(step, db_name, serv_as):
    server = getattr(world, serv_as)
    LOG.info("Create database %s in %s" % (db_name, server.id))
    world.db.insert_data_to_database(db_name, server)


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
        if not info['servers']['master']['serverId'] == master.id:
            raise AssertionError('Master is not %s' % master_serv)
        for sl in info['servers']:
            if sl.startswith('slave'):
                if info['servers'][sl]['serverId'] == slave.id:
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


@step('([\w]+)( not)? contains database (.+)$')
def check_database_in_new_server(step, serv_as, has_not, db_name):
    has_not = has_not and True or False
    time.sleep(5)
    dbs = db_name.split(',')
    if serv_as == 'all':
        world.farm.servers.reload()
        servers = filter(lambda s: s.status == ServerStatus.RUNNING, world.farm.servers)
    else:
        servers = [getattr(world, serv_as)]
    for server in servers:
        for db in dbs:
            LOG.info('Check database %s in server %s' % (db, server.id))
            world.assert_not_equal(world.db.database_exist(db, server), not has_not,
                                   (has_not and 'Database %s exist in server %s, but must be erased.  All db: %s'
                                   or 'Database %s not exist in server %s, all db: %s')
                                   % (db_name, server.id, world.db.database_list(server)))


@step('I create database (.+) on (.+)')
def create_new_database(step, db_name, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Create database %s in %s' % (db_name, server.id))
    world.db.database_create(db_name, server)
    LOG.info('Database was success create')
    time.sleep(60)


@step('And databundle type in ([\w\d]+) is ([\w]+)')
def check_bundle_type(step, serv_as, bundle_type):
    LOG.info('Check databundle type')
    time.sleep(10)
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
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

@step('I know last backup url$')
def get_last_backup_url(step):
    LOG.info('Get last backup date')
    last_backup = world.farm.db_info(world.role_type)['last_backup']
    last_backup = last_backup - timedelta(seconds=last_backup.second)
    LOG.info('Last backup date is: %s' % last_backup)
    all_backups = IMPL.services.list_backups(world.farm.id)
    last_backup_url = IMPL.services.backup_details(
        all_backups[last_backup]['backup_id']
    )['links']['1']['path']['dirname']
    last_backup_url = 's3://%s/manifest.json' % last_backup_url
    LOG.info('Last backup URL: %s' % last_backup_url)
    setattr(world, 'last_backup_url', last_backup_url)


@step('I know timestamp from ([\w\d]+) in ([\w\d]+)$')
def save_timestamp(step, db, serv_as):
    server = getattr(world, serv_as)
    cursor = world.db.get_cursor(server)
    cursor.execute('USE %s;' % db)
    cursor.execute('SELECT * FROM timestamp;')
    timestamp = cursor.fetchone()[0]
    setattr(world, 'backup_timestamp', timestamp)


@step('I download backup in ([\w\d]+)')
def download_dump(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.put_file('/tmp/download_backup.py', resources('scripts/download_backup.py').get())
    if CONF.main.driver == Platform.EC2:
        if node.os[0] == 'redhat' and node.os[1].startswith('5'):
            node.run('python26 /tmp/download_backup.py --platform=ec2 --key=%s --secret=%s --url=%s' % (
                world.cloud.config.libcloud.key, world.cloud.config.libcloud.secret, world.last_backup_url
            ))
        else:
            node.run('python /tmp/download_backup.py --platform=ec2 --key=%s --secret=%s --url=%s' % (
                world.cloud.config.libcloud.key, world.cloud.config.libcloud.secret, world.last_backup_url
            ))
    # elif CONF.main.driver == Platform.GCE:
    #     with open(world.cloud.config.libcloud.key, 'r+') as key:
    #         node.put_file('/tmp/gcs_pk.p12', key.readall())
    #     node.run('python /tmp/download_backup.py --platform=gce --key=%s --url=%s' % (world.cloud.config.libcloud.username,
    #                                                                                   world.last_backup_url))
    # elif CONF.main.driver == Platform.RACKSPACE_US:
    #     node.run('python /tmp/download_backup.py --platform=rackspaceng --key=%s --secret=%s --url=%s' % (
    #         world.cloud.config.libcloud.key, world.cloud.config.libcloud.secret, world.last_backup_url
    #     ))


@step('I delete databases ([\w\d,]+) in ([\w\d]+)$')
def delete_databases(step, databases, serv_as):
    databases = databases.split(',')
    server = getattr(world, serv_as)
    LOG.info('Delete databases  %s in server %s' % (databases, server.id))
    for db in databases:
        LOG.info('Delete database: %s' % db)
        world.db.database_delete(db, server)


@step('I restore databases ([\w\d,]+) in ([\w\d]+)$')
def restore_databases(step, databases, serv_as):
    databases = databases.split(',')
    server = getattr(world, serv_as)
    LOG.info('Restore databases  %s in server %s' % (databases, server.id))
    node = world.cloud.get_node(server)
    backups_in_server = node.run('ls /tmp/dbrestore/*')[0].split()
    LOG.info('Available backups in server: %s' % backups_in_server)
    for db in databases:
        LOG.info('Restore database %s' % db)
        path = '/tmp/dbrestore/%s' % db
        if not path in backups_in_server:
            raise AssertionError('Database %s backup not exist in path %s' % (db, path))
        world.db.database_create(db, server)
        out = node.run('mysql -u scalr -p%s %s < %s' % (world.db.password, db, path))
        if out[1]:
            raise AssertionError('Get error on restore database %s: %s' % (db, out[1]))


@step("database ([\w\d]+) in ([\w\d]+) contains '([\w\d]+)' with (\d+) lines$")
def check_database_table(step, db, serv_as, table_name, line_count):
    #TODO: Support to all databases
    server = getattr(world, serv_as)
    assert world.db.database_exist(db, server) == True, 'Database %s not exist in server %s' % (db, server.id)
    cursor = world.db.get_cursor(server)
    cursor.execute('USE %s;' % db)
    cursor.execute('SHOW TABLES;')
    tables = [t[0] for t in cursor.fetchall()]
    if not table_name in tables:
        raise AssertionError('Table %s not exist in database: %s' % (table_name, db))
    count = cursor.execute('SELECT * FROM %s;' % table_name)
    if not int(count) == int(line_count):
        raise AssertionError('In table %s lines, but must be: %s' % (count ,line_count))


@step('database ([\w\d]+) in ([\w\d]+) has relevant timestamp$')
def check_timestamp(step, db, serv_as):
    server = getattr(world, serv_as)
    cursor = world.db.get_cursor(server)
    cursor.execute('USE %s;' % db)
    cursor.execute('SELECT * FROM timestamp;')
    timestamp = cursor.fetchone()[0]
    if not timestamp == getattr(world, 'backup_timestamp', timestamp):
        raise AssertionError('Timestamp is not equivalent: %s != %s' % (timestamp, getattr(world, 'backup_timestamp', timestamp)))


@step(r'([\w\d]+) replication status is ([\w\d]+)')
def verify_replication_status(step, behavior, status):
    wait_until(world.wait_replication_status, args=(behavior, status), error_text="Replication in broken", timeout=600)
