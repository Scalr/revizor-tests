import os
import re
import time
import socket
import urllib2
import logging
from datetime import datetime

import requests
from lettuce import world

from revizor2.api import Farm, IMPL
from revizor2.fixtures import resources
from revizor2.conf import CONF, roles_table
from revizor2.consts import ServerStatus, Platform
from revizor2.exceptions import ScalarizrLogError, ServerTerminated

import httplib

LOG = logging.getLogger()

@world.absorb
def give_empty_running_farm():
    farm_id = os.environ.get('RV_FARM_ID', CONF.main.farm_id)
    world.farm = Farm.get(farm_id)
    world.farm.roles.reload()
    if len(world.farm.roles):
        IMPL.farm.clear_roles(world.farm.id)
    world.farm.vhosts.reload()
    world.farm.domains.reload()
    for vhost in world.farm.vhosts:
        LOG.info('Delete vhost: %s' % vhost.name)
        vhost.delete()
    for domain in world.farm.domains:
        LOG.info('Delete domain: %s' % domain.zone_name)
        domain.delete()
    world.farm.vhosts.reload()
    world.farm.domains.reload()
    for vhost in world.farm.vhosts:
        LOG.info('Delete vhost: %s' % vhost.name)
        vhost.delete()
    for domain in world.farm.domains:
        LOG.info('Delete domain: %s' % domain.zone_name)
        domain.delete()
    if world.farm.terminated:
        world.farm.launch()
    LOG.info('Return empty running farm: %s' % world.farm.id)


@world.absorb
def add_role_to_farm(role_type=None, options=None, scripting=None, storages=None):
    role = None
    if CONF.main.role_id:
        role = roles_table[CONF.main.role_id]
    elif role_type:
        role = roles_table.filter({'behavior': role_type}).first()
    else:
        role = roles_table.filter().first()
    if not role:
        raise AssertionError('Not find role in roles table')
    old_roles_ids = [r.id for r in world.farm.roles]
    LOG.info('Add role %s to farm' % role)
    world.farm.add_role(role.keys()[0], options=options, scripting=scripting, storages=storages)
    LOG.info('Add role %s to farm %s\n options: %s\n scripting: %s' % (role.keys()[0], world.farm.id, options, scripting))
    time.sleep(5)
    world.farm.roles.reload()
    for r in world.farm.roles:
        if not r.id in old_roles_ids:
            return r
    return None


@world.absorb
def add_roles_to_farm(roles_type=None, options=None):
    roles = []
    for r in roles_type:
        LOG.info('Add role with behavior %s to farm' % r)
        role = roles_table.filter({'behavior': r}).first()
        LOG.debug('Added role: %s' % role)
        roles.append(role.keys()[0])
    world.farm.add_role(roles, options=options)


@world.absorb
def check_server_status(status, role_id, one_serv_in_farm=False, **kwargs):
    #TODO: rewrite this because it's UGLY
    time.sleep(5)
    LOG.debug('Check server in farm %s and role_id %s' % (world.farm.id, role_id))
    status = ServerStatus.from_code(status)
    LOG.debug('Update servers')
    world.farm.servers.reload()
    servers = world.farm.servers
    serv = getattr(world, '_temp_serv', None)
    if serv:
        LOG.info('Server get: %s' % serv.id)
    else:
        LOG.debug('No server')
    node = getattr(world, '_temp_serv_node', None)
    LOG.debug('Node get: %s' % node)
    if node:
        if not node.public_ip:
            node = None
    if node is None and serv:
        for server in servers:
            if server.id == serv.id and server.cloud_server_id:
                LOG.debug("Create node from server: %s, cloud id: %s" % (serv.id, server.cloud_server_id))
                node = world._temp_serv_node = world.cloud.get_node(server)
    for server in servers:
        LOG.debug('Iterate server %s in farm, state: %s' % (server.id, server.status))
        if server.role_id == role_id and not server.status == ServerStatus.TERMINATED and not server.status == ServerStatus.PENDING_TERMINATE:
            if serv:
                LOG.info('Check server %s' % serv.id)
                if serv.id == server.id:
                    LOG.info('Founded server %s have status: %s' % (server.id, server.status))
                    if node:
                        try:
                            out = ''
                            LOG.info('Check scalarizr log in server %s' % serv.id)
                            out = node.run('grep "ERROR\|Traceback" /var/log/scalarizr_debug.log ')
                            LOG.debug('Grep result: %s' % out)
                            out = out[0]
                        except BaseException, e:
                            LOG.warning('Can\'t connect to server %s' % serv.id)
                            LOG.warning('Exception: %s' % e)
                        else:
                            for line in out.splitlines():
                                log_date = None
                                log_level = None
                                now = datetime.now()
                                try:
                                    log_date = datetime.strptime(line.split()[0], '%Y-%m-%d')
                                    log_level = line.strip().split()[3]
                                except (ValueError, IndexError):
                                    pass
                                if log_date:
                                    if not log_date.year == now.year \
                                    or not log_date.month == now.month \
                                    or not log_date.day == now.day:
                                        continue
                                elif 'boto' in line or 'p2p_message' in line:
                                    continue
                                elif 'Caught exception reading instance data' in out:
                                    break
                                if log_level == 'ERROR':
                                    LOG.error('Find error in scalarizr log')
                                    LOG.error('Errors: %s' % out)
                                    raise ScalarizrLogError("Error in scalarizr log for server %s" % serv.id)
                            LOG.info('Not found any problem in scalarizr_debug.log')
                    LOG.info('Server %s in state: %s' % (server.id, server.status))
                    if ServerStatus.from_code(server.status) == status:
                        if status == ServerStatus.RUNNING:
                            world._temp_serv = None
                            world._temp_serv_node = None
                        LOG.info('Server is in state %s complete' % status)
                        return server
                    elif status == ServerStatus.INIT and ServerStatus.from_code(server.status) == ServerStatus.RUNNING:
                        LOG.info('Server wait Initializing, but actually has status - Running')
                        return server
                    elif ServerStatus.from_code(server.status) == ServerStatus.TERMINATED:
                        raise ServerTerminated('Scalr killed this "%s" server, because it have status: %s' % (server.id, server.status))
            elif server.status == ServerStatus.PENDING or\
                                                                    server.status == ServerStatus.PENDING_LAUNCH or\
                                                                    server.status == ServerStatus.INIT:
                LOG.info('Found server %s in farm %s' % (server.id, world.farm.id))
                world._temp_serv = server
            elif one_serv_in_farm and server.status == ServerStatus.RUNNING:
                world._temp_serv = None
                world._temp_serv_node = None
                return server
    return False


@world.absorb
def wait_servers_running(role_id, count):
    world.farm.servers.reload()
    run_count = 0
    for server in world.farm.servers:
        if server.role_id == role_id and server.status == ServerStatus.RUNNING:
            LOG.info('Server %s is Running' % server.id)
            run_count += 1
    if int(count) == run_count:
        LOG.info('Servers in running state are %s' % run_count)
        return True
    return False


@world.absorb
def wait_farm_terminated(*args, **kwargs):
    farm = world.farm
    farm.servers.reload()
    for server in farm.servers:
        if server.status == ServerStatus.TERMINATED:
            continue
        else:
            return False
    return True


@world.absorb
def check_message_status(status, server, msgtype='sends', **kwargs):
    old_message_id = getattr(world, '%s_old_message_id' % server.id, 0)
    LOG.debug("Old message id: %s" % old_message_id)
    message_type = 'out' if msgtype.strip() == 'sends' else 'in'
    msg_id = getattr(world, 'msg_temp_id', None)
    server.messages.reload()
    for message in server.messages:
        LOG.debug('Work with message: %s %s %s %s %s %s' % (message.id, message.msgtype, message.messageid,
                                                         message.message, message.msgname, message.delivered))
        if int(message.id) <= int(old_message_id):
            continue
        if message.id == msg_id:
            LOG.debug('Message is founded: %s' % message.id)
            if message.delivered:
                LOG.debug('Message is delivered, return server')
                del world.msg_temp_id
                setattr(world, '%s_old_message_id' % server.id, message.id)
                return server
        else:
            LOG.debug('Find message \'%s\', but processing \'%s\'' % (status, message.msgname))
            if message.msgname == status:
                LOG.debug('Check to/from: %s %s' % (message_type, message.msgtype))
                if msgtype:
                    if message.msgtype == message_type:
                        setattr(world, 'msg_temp_id', message.id)
                    else:
                        continue
                else:
                    setattr(world, 'msg_temp_id', message.id)
                    if message.delivered:
                        del world.msg_temp_id
                        setattr(world, '%s_old_message_id' % server.id, message.id)
                        return server
    return False


@world.absorb
def check_message_in_server_list(status, servers, msgtype=None):
    mt = 'out' if msgtype == 'sends' else 'in'
    LOG.debug("Find message: %s %s" % (status, msgtype))
    for server in servers:
        LOG.info('Find message in server %s' % server.id)
        server.messages.reload()
        for mes in server.messages:
            LOG.debug('Work with message: %s %s %s %s %s %s' % (mes.id, mes.msgtype, mes.messageid,
                                                                mes.message, mes.msgname, mes.delivered))
            LOG.debug('Check message: %s %s' % (status, mes.msgname))
            if mes.msgname == status:
                LOG.debug('Check to/from: %s %s' % (mt, mes.msgtype))
                if msgtype:
                    if mt == mes.msgtype:
                        return server
                    else:
                        continue
                else:
                    return server
    return False


@world.absorb
def bundle_task_created(server, bundle_id):
    for bundlelog in server.bundlelogs:
        if bundlelog.id == bundle_id:
            contents = bundlelog.contents
            for log in contents:
                if 'Bundle task created' in log['message']:
                    LOG.info('New bundle task id: %s' % bundle_id)
                    return True
                elif 'Bundle task status changed to: failed' in log['message']:
                    LOG.error('Bundle task %s is failed' % bundle_id)
                    raise AssertionError(log['message'])
    return AssertionError("No find bundle log")


@world.absorb
def bundle_task_completed(server, bundle_id, *args, **kwargs):
    server.bundlelogs.reload()
    for bundlelog in server.bundlelogs:
        if bundlelog.id == bundle_id:
            contents = bundlelog.contents
            for log in contents:
                if 'Bundle task status: success' in log['message']:
                    for l in contents:
                        if 'Role ID:' in l['message']:
                            world.new_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
                    LOG.info('Bundle task %s is complete. New role id: %s' % (bundle_id, world.new_role_id))
                    return True
                elif 'Bundle task status changed to: failed' in log['message']:
                    raise AssertionError(log['message'])
    return False


@world.absorb
def wait_script_execute(server, message, state):
    LOG.info('Find message %s and state %s in scripting logs' % (message, state))
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        if message in log.message and state == log.event:
            return True
    return False


@world.absorb
def bundle_task_complete_rolebuilder(bundle_id):
    logs = IMPL.bundle.logs(bundle_id)
    for log in logs:
        if 'Bundle task status: success' in log['message']:
            return True
        elif 'Bundle task status changed to: failed' in log['message']:
            raise AssertionError(log['message'])
    return False


@world.absorb
def check_resolving(domain):
    LOG.debug('Try resolve domain %s' % domain)
    try:
        ip = socket.gethostbyname(domain)
        LOG.info('Domain resolved to %s' % ip)
        return ip
    except socket.gaierror:
        LOG.debug('Domain not resolved')
        return False


@world.absorb
def check_open_port(server, port):
    LOG.debug('Check open port %s:%s' % (server, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    try:
        s.connect((server.public_ip, int(port)))
        s.shutdown(2)
        return True
    except socket.error:
        return False


@world.absorb
def get_hostname(server):
    serv = world.cloud.get_node(server)
    out = serv.run('/bin/hostname')
    return out[0]


@world.absorb
def wait_upstream_in_config(node, ip, contain=True):
    out = node.run('cat /etc/nginx/app-servers.include')
    if contain:
        if ip in "".join([str(i) for i in out]):
            return True
        else:
            return False
    else:
        if not ip in "".join([str(i) for i in out]):
            return True
        else:
            return False


@world.absorb
def check_index_page(node, proto, domain, name):
    index = resources('html/index_test.php')
    index = index.get() % {'id': name}
    nodes = node if isinstance(node, (list, tuple)) else [node]
    for n in nodes:
        LOG.debug('Upload index page %s to server %s' % (name, n.public_ip))
        n.run('mkdir /var/www/%s' % name)
        n.put_file(path='/var/www/%s/index.php' % name, content=index)
    try:
        LOG.info('Try get index from domain: %s://%s' % (proto, domain))
        resp = requests.get('%s://%s/' % (proto, domain), timeout=15, verify=False).text
    except Exception, e:
        raise AssertionError('Exception in opened page: %s %s' % (domain, e))
    if 'VHost %s added' % name in resp:
        return True
    raise AssertionError('Index page not valid: %s' % resp)


@world.absorb
def wait_rabbitmq_cp(*args, **kwargs):
    detail = world.farm.rabbitmq_cp_detail
    if not detail or not 'password' in detail:
        return False
    else:
        return detail


@world.absorb
def wait_rabbitmq_cp_url(*args, **kwargs):
    detail = world.farm.rabbitmq_cp_detail
    if not detail or not 'url' in detail:
        return False
    else:
        return detail


@world.absorb
def wait_site_response(domain, msg, proto='http', **kwargs):
    try:
        p = urllib2.urlopen("%s://%s" % (proto, domain))
        p = p.read()
    except urllib2.HTTPError:
        return False
    if msg in p:
        return True
    return False


@world.absorb
def mongodb_wait_data(conn, data, **kwargs):
    db = getattr(conn, data['db'])
    if db.keys.count() > 0:
        res = db.keys.find(id=data['id'])[0]
        if 'testkey' in res:
            if res['testkey'] == 'myvalue':
                return True
    return False


@world.absorb
def mongodb_wait_data2(node, data):
    #TODO: rewrite it and use only python!
    node.put_file(path='/root/mongoslave.js', content=resources('scripts/mongoslave.js').get())
    res = node.run('mongo localhost:27018 < /root/mongoslave.js')
    node.run('rm /root/mongoslave.js')
    if not str(data['id']) in res[0]:
        return False
    return True


@world.absorb
def wait_database(db_name, server):
    return world.db.database_exist(db_name, server)


@world.absorb
def wait_replication_status(behavior, status):
    db_status = world.farm.db_info(behavior)
    for server in db_status['servers']:
        LOG.info("Check replication in server %s it is: %s" % (db_status['servers'][server]['serverId'], db_status['servers'][server]['replication']['status']))
        if not db_status['servers'][server]['replication']['status'].strip() == status.strip():
            LOG.debug("Replication on server %s is %s" % (db_status['servers'][server]['serverId'], db_status['servers'][server]['replication']['status']))
            return False
    return True


@world.absorb
def check_server_storage(serv_as, status):
    server = getattr(world, serv_as)
    volumes = server.get_volumes()
    LOG.debug('Volumes for server %s is: %s' % (server.id, volumes))
    if CONF.main.platform == 'ec2':
        storages = filter(lambda x: 'sda' not in x.extra['device'], volumes)
    elif CONF.main.platform in ['cloudstack', 'idcf', 'ucloud']:
        storages = filter(lambda x: x.extra['type'] == 'DATADISK', volumes)
    if not storages and not status.strip() == 'deleted':
        raise AssertionError('Server %s not have storages' % server.id)
    if status.strip() == 'deleted' and len(storages) < len(getattr(world, '%s_storages' % serv_as)):
        return True
    for vol in volumes:
        if CONF.main.platform == 'ec2':
            state = 'used' if vol.extra['state'] in ['in-use', 'available'] else 'deleted'
        elif CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
            state = 'used'
        if status == 'use' and state == 'used':
            return True
        elif status == 'deleted' and not state == 'deleted':
            return False
    return True


@world.absorb
def get_szr_messages(node):
    LOG.info('Get messages list from server %s' % node.id)
    out = node.run('szradm list-messages')

    if out[0] in ('', ' '):
        return []
    lines = out[0].splitlines()
    # remove horizontal borders
    lines = filter(lambda x: not x.startswith("+"), lines)
    # split each line

    def split_tline(line):
        return map(lambda x: x.strip("| "), line.split(" | "))

    lines = map(split_tline, lines)
    # get column names
    head = lines.pop(0)

    # [{column_name: value}]
    messages = [dict(zip(head, line)) for line in lines]
    LOG.info('Server messages: %s' % messages)
    return messages


@world.absorb
def check_text_in_scalarizr_log(node, text):
    out = node.run("cat /var/log/scalarizr_debug.log | grep '%s'" % text)[0]
    if text in out:
        return True
    return False


@world.absorb
def check_mongo_status(status):
    if world.farm.db_info('mongodb')['status'] == status:
        return True
    return False


@world.absorb
def assert_exist(first, message='Equal'):
    '''Assert if first exist'''
    assert not first, message


@world.absorb
def assert_not_exist(first, message='Equal'):
    '''Assert if first not exist'''
    assert first, message


@world.absorb
def assert_equal(first, second, message='Equal'):
    '''Assert if first==second'''
    assert not first == second, message

@world.absorb
def assert_not_equal(first, second, message='Not equal'):
    '''Assert if not first==second'''
    assert first == second, message

@world.absorb
def assert_in(first, second, message=''):
    '''Assert if first in second'''
    assert not first in second, message

@world.absorb
def assert_not_in(first, second, message=''):
    '''Assert if not first in second'''
    assert first in second, message

@world.absorb
def set_iptables_rule(role_type, server, port):
    """Set iptables rule in the top of the list (str, str, list||tuple)->"""
    LOG.info('Role is %s, add iptables rule for me' % role_type)
    node = world.cloud.get_node(server)
    try:
        my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
    except httplib.BadStatusLine:
        time.sleep(5)
        my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
    LOG.info('My IP address: %s' % my_ip)
    if isinstance(port, (tuple, list)):
        if len(port) == 2:
            port = ':'.join(str(x) for x in port)
        else:
            port = ','.join(str(x) for x in port)
    node.run('iptables -I INPUT -p tcp -s %s --dport %s -j ACCEPT' % (my_ip,port))

