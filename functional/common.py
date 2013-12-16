import os
import re
import time
import socket
import urllib2
import logging
import traceback
from datetime import datetime

import requests
from lettuce import world

from revizor2.api import Farm, IMPL
from revizor2.fixtures import resources
from revizor2.conf import CONF, roles_table
from revizor2.consts import ServerStatus, Platform, MessageStatus
from revizor2.exceptions import ScalarizrLogError, ServerTerminated, ServerFailed, TimeoutError, MessageNotFounded, MessageFailed
from revizor2.helpers.jsonrpc import SzrApiServiceProxy

import httplib

LOG = logging.getLogger('common')

SCALARIZR_LOG_IGNORE_ERRORS = ['boto', 'p2p_message', 'Caught exception reading instance data']


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
        LOG.info('Delete domain: %s' % domain.name)
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


def verify_scalarizr_log(node):
    LOG.info('Verify scalarizr log in server: %s' % node.id)
    try:
        log_out = node.run('grep "ERROR\|Traceback" /var/log/scalarizr_debug.log ')
        LOG.debug('Grep result: %s' % log_out[0])
    except BaseException, e:
        LOG.error('Can\'t connect to server: %s' % e)
        LOG.error(traceback.format_exc())
        return
    for line in log_out[0].splitlines():
        LOG.debug('Verify line "%s" for errors' % line)
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

        for error in SCALARIZR_LOG_IGNORE_ERRORS:
            if error in line:
                continue

        if log_level == 'ERROR':
            LOG.error('Found ERROR in scalarizr_debug.log: %s' % log_out[0])
            raise ScalarizrLogError('Error in scalarizr_debug.log on server %s' % node.id)


@world.absorb
def wait_server_bootstrapping(role, status=ServerStatus.RUNNING, timeout=2100):
    """
    Wait new server in role and remember which servers was bootstrapping, return Server
    """
    status = ServerStatus.from_code(status)

    LOG.info('Launch process looking for new server in farm %s for role %s, wait status %s' %
             (world.farm.id, role.role.name, status))

    previous_servers = getattr(world, '_previous_servers', [])
    if not previous_servers:
        world._previous_servers = previous_servers

    LOG.debug('Previous servers: %s' % previous_servers)

    lookup_server = None
    lookup_node = None

    start_time = time.time()

    while time.time() - start_time < timeout:
        if not lookup_server:
            LOG.debug('Reload servers in role')
            role.servers.reload()
            for server in role.servers:
                LOG.debug('Work with server: %s - %s' % (server.id, server.status))
                if not server in previous_servers and server.status in [ServerStatus.PENDING_LAUNCH,
                                                                        ServerStatus.PENDING,
                                                                        ServerStatus.INIT,
                                                                        ServerStatus.RUNNING]:
                    LOG.debug('I found a server: %s' % server.id)
                    lookup_server = server
        if lookup_server:
            LOG.debug('Reload lookup_server')
            lookup_server.reload()

            LOG.debug('Check lookup server terminated?')
            if lookup_server.status in [ServerStatus.TERMINATED, ServerStatus.PENDING_TERMINATE]\
                and not status in [ServerStatus.TERMINATED, ServerStatus.PENDING_TERMINATE]:
                raise ServerTerminated('Server %s change status to %s' % (lookup_server.id, lookup_server.status))

            LOG.debug('Check lookup server launch failed')
            if lookup_server.is_launch_failed:
                raise ServerFailed('Server %s failed in %s' % (lookup_server.id, ServerStatus.PENDING_LAUNCH))

            LOG.debug('Check lookup server init failed')
            if lookup_server.is_init_failed:
                raise ServerFailed('Server %s failed in %s' % (lookup_server.id, ServerStatus.INIT))

            LOG.debug('Try get node')
            if not lookup_node and not lookup_server.status in [ServerStatus.PENDING_LAUNCH,
                                                                ServerStatus.PENDING_TERMINATE,
                                                                ServerStatus.TERMINATED]:
                LOG.debug('Try to get node object for lookup server')
                lookup_node = world.cloud.get_node(lookup_server)

            LOG.debug('Verify debug log')
            if lookup_node:
                LOG.debug('Check scalarizr log in lookup server')
                verify_scalarizr_log(lookup_node)

            LOG.debug('If server Running and we wait Initializing, return server')
            if status == ServerStatus.INIT and lookup_server.status == ServerStatus.RUNNING:
                LOG.info('We wait Initializing but server already Running')
                status == ServerStatus.RUNNING

            LOG.debug('Compare server status')
            if lookup_server.status == status:
                LOG.info('Lookup server in right status now: %s' % lookup_server.status)
                if status == ServerStatus.RUNNING:
                    LOG.debug('Insert server to previous servers')
                    previous_servers.append(lookup_server)
                LOG.debug('Return server %s' % lookup_server)
                return lookup_server
        LOG.debug('Sleep 10 seconds')
        time.sleep(10)
    else:
        if lookup_server:
            raise TimeoutError('Server %s not in state "%s" it has status: "%s"' % (lookup_server.id, status, lookup_server.status))
        raise TimeoutError('New server in role "%s" was not founding' % role)



@world.absorb
def wait_servers_running(role_id, count):
    world.farm.servers.reload()
    previous_servers = getattr(world, '_previous_servers', [])
    run_count = 0
    for server in world.farm.servers:
        if server.role_id == role_id and server.status == ServerStatus.RUNNING:
            LOG.info('Server %s is Running' % server.id)
            if not server in previous_servers:
                previous_servers.append(server)
            run_count += 1
    if int(count) == run_count:
        LOG.info('Servers in running state are %s' % run_count)
        world._previous_servers = previous_servers
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
def wait_server_message(server, message_name, message_type='out', find_in_all=False, timeout=600):
    """
    Wait message in server list (or one server). If find_in_all is True, wait this message in all
    servers.
    """
    def check_message_in_server(server, message_name, message_type):
        server.messages.reload()
        for message in server.messages:
            LOG.debug('Work with message: %s / %s - %s (%s) on server %s ' %
                      (message.type, message.name, message.delivered, int(message.id), server.id))
            if server._last_internal_message and int(message.id) <= int(server._last_internal_message.id):
                LOG.debug('This message <= when last internal message: %s <= %s' % (int(message.id), int(server._last_internal_message.id)))
                continue
            if message.name == message_name and message.type == message_type:
                LOG.info('This message matching the our pattern')
                if message.delivered:
                    LOG.info('Lookup message delivered')
                    server._last_internal_message = message
                    return True
                elif message.status == MessageStatus.FAILED:
                    raise MessageFailed('Message %s / %s (%s) failed' % (message.type, message.name, message.messageid))
                elif message.status == MessageStatus.UNSUPPORTED:
                    raise MessageFailed('Message %s / %s (%s) unsupported' % (message.type, message.name, message.messageid))
        return False

    message_type = 'out' if message_type.strip() == 'sends' else 'in'

    if not isinstance(server, (list, tuple)):
        servers = [server]
    else:
        servers = server

    LOG.info('Try found message %s / %s in servers %s' % (message_type, message_name, servers))

    start_time = time.time()

    delivered_servers = []

    while time.time() - start_time < timeout:
        if not find_in_all:
            for serv in servers:
                if check_message_in_server(serv, message_name, message_type):
                    return serv
        else:
            if delivered_servers == servers:
                LOG.info('All servers has delivered message: %s / %s' % (message_type, message_name))
                return True
            for serv in servers:
                if serv in delivered_servers:
                    continue
                result = check_message_in_server(serv, message_name, message_type)
                if result:
                    delivered_servers.append(serv)
    else:
        raise MessageNotFounded('%s / %s was not finding in servers: %s' % (message_type,
                                                                            message_name,
                                                                            [s.id for s in servers]))


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
def check_index_page(node, proto, revert, domain_name, name):
    index = resources('html/index_test.php')
    index = index.get() % {'id': name}
    if proto.isdigit():
        url = 'http://%s:%s/' % (domain_name, proto)
    else:
        url = '%s://%s/' % (proto, domain_name)
    nodes = node if isinstance(node, (list, tuple)) else [node]
    for n in nodes:
        LOG.debug('Upload index page %s to server %s' % (name, n.public_ip))
        n.run('mkdir /var/www/%s' % name)
        n.put_file(path='/var/www/%s/index.php' % name, content=index)
    for i in range(3):
        LOG.info('Try get index from URL: %s, attempt %s ' % (url, i+1))
        try:
            resp = requests.get(url, timeout=30, verify=False)
            break
        except Exception, e:
            LOG.warning("Error in openning page '%s': %s" % (url, e))
            time.sleep(5)
    else:
        raise AssertionError("Can't get index page: %s" % url)
    if ('VHost %s added' % name in resp.text) or (revert and resp.status_code == 200):
        return True
    raise AssertionError('Index page not valid: %s. Status code: %s' % (resp.text, resp.status_code))


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
        if not db_status['servers'][server]['status'] == ServerStatus.RUNNING:
            LOG.warning('Server %s is not running it %s' % (db_status['servers'][server]['serverId'], db_status['servers'][server]['status']))
            continue
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
    node.run('iptables -I INPUT -p tcp -s %s --dport %s -j ACCEPT' % (my_ip, port))


@world.absorb
def kill_process_by_name(server, process):
    """Kill process on remote host by his name (server(obj),str)->None if success"""
    LOG.info('Kill %s process on remote host %s' % (process, server.public_ip))
    return world.cloud.get_node(server).run("pgrep -l %(process)s | awk {print'$1'} | xargs -i{}  kill {} && sleep 5 && pgrep -l %(process)s | awk {print'$1'}" % {'process': process})[0]


@world.absorb
def change_service_status(server, service, status, is_api=False, pid=False):
    """change_service_status(status, service, server) Change process status on remote host by his name
    Return pid before change status, pid after change status, exit code

    @type   status: str
    @param  status: Service status start, stop, restart, etc or api methods service_restart

    @type   service: dict
    @param  service: {node: name, api: name}, Service node name - scalarizr, apache2, etc...,
                     service api endpoint name apahe, etc...

    @type   server: obj
    @param  server: Server object

    @type   is_api:   bool
    @param  is_api:   Status is api call or node command

    @type   pid:   bool
    @param  pid:   Status is change pid for node service
    """
    #Init params
    node = world.cloud.get_node(server)
    if is_api:
        api = SzrApiServiceProxy(server.public_ip, str(server.details['scalarizr.key']))

    #Get process pid
    get_pid = lambda: node.run("pgrep -l %(process)s | awk {print'$1'} && sleep 5" % {'process': service['node']})[0].rstrip('\n').split('\n')
    #Change process status
    change_status = lambda: node.run("service %(process)s %(status)s && sleep 5" % {'process': service['node'], 'status': status})\
        if not is_api\
        else getattr(getattr(api, service['api']), status)()
    #Action list
    change_pid = {
        True: ({'pid_before': get_pid}, {'info': change_status}, {'pid_after': get_pid}),
        False: ({'pid_before': None}, {'info': change_status}, {'pid_after': get_pid}),
    }
    try:
        return dict([key, func() if func else ['']] for item in change_pid[pid] for key, func in item.iteritems())
    except Exception as e:
        error_msg = """An error occurred while trying to execute a command %(command)s.
                    Original error: %(error)s""" % {
                        'error': e,
                        'command': '%s.%s()' % (service['api'], status)}
        LOG.error(error_msg)
        raise Exception(error_msg)


@world.absorb
def is_log_rotate(server, process, rights, group='nogroup'):
    """Checks for logrotate config file and rotates the log. Returns the status of the operation."""
    LOG.info('Loking for config file:  %s-logrotate on remote host %s' % (process, server.public_ip))
    node = world.cloud.get_node(server)
    logrotate_conf = node.run('cat /etc/logrotate.d/%s-logrotate' % process)
    if not logrotate_conf[1]:
        logrotate_param = {}
        #Get the directory from the first line config file
        logrotate_param['dir'] = '/'.join(logrotate_conf[0].split('\n')[0].split('/')[0:-1])
        #Check the archive log files
        logrotate_param['compress'] = 'compress' in logrotate_conf[0]
        #Get the log file mask from the first line config
        logrotate_param['log_mask'] = logrotate_conf[0].split('\n')[0].split('/')[-1].rstrip('.log {')
        #Performing rotation and receive a list of log files
        LOG.info('Performing rotation and receive a list of log files for % remote host %s' % (process, server.public_ip))
        rotated_logs = node.run('logrotate -f /etc/logrotate.d/%s-logrotate && stat --format="%%n %%U %%G %%a"  %s/%s' %
                                (process, logrotate_param['dir'], logrotate_param['log_mask']))
        if not rotated_logs[2]:
            try:
                log_files = []
                for str in rotated_logs[0].rstrip('\n').split('\n'):
                    tmp_str = str.split()
                    log_files.append(dict([['rights', tmp_str[3]], ['user', tmp_str[1]], ['group', tmp_str[2]],  ['file', tmp_str[0]]]))
                    has_gz = False
                for log_file_atr in log_files:
                    if log_file_atr['file'].split('.')[-1] == 'gz' and not has_gz:
                        has_gz = True
                    if not (log_file_atr['rights'] == rights and
                            log_file_atr['user'] == process and
                            log_file_atr['group'] == group):
                        raise AssertionError("%(files)s file attributes are not correct. Wrong attributes %(atr)s: " %
                                             {'file': log_file_atr['file'], 'atr': (log_file_atr['rights'],
                                                                                    log_file_atr['user'],
                                                                                    log_file_atr['group'])})
                if logrotate_param['compress'] and not has_gz:
                    raise AssertionError('Logrotate config file has attribute "compress", but not gz find.')
            except IndexError, e:
                raise Exception('Error occurred at get list of log files: %s' % e)
        else:
            raise AssertionError("Can't logrotate to force the rotation. Error message:%s" % logrotate_conf[1])
    else:
        raise AssertionError("Can't get config file:%s-logrotate. Error message:%s" %
                             (process, logrotate_conf[1]))
    return True


