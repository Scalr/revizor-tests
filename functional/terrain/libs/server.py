__author__ = 'gigimon'

import time
import logging
import traceback
from datetime import datetime

import requests
from lettuce import world
from libcloud.compute.types import NodeState

from revizor2.api import Server
from revizor2.fixtures import resources
from revizor2.consts import ServerStatus, MessageStatus, Dist
from revizor2.exceptions import ScalarizrLogError, ServerTerminated, ServerFailed, TimeoutError, MessageNotFounded, MessageFailed
from revizor2.helpers.jsonrpc import SzrApiServiceProxy

LOG = logging.getLogger(__name__)


SCALARIZR_LOG_IGNORE_ERRORS = ['boto', 'p2p_message', 'Caught exception reading instance data']


@world.absorb
def verify_scalarizr_log(node):
    if isinstance(node, Server):
        node = world.cloud.get_node(node)
    LOG.info('Verify scalarizr log in server: %s' % node.id)
    try:
        log_out = node.run('grep "ERROR" /var/log/scalarizr_debug.log ')
        LOG.debug('Grep result: %s' % log_out[0])
    except BaseException, e:
        LOG.error('Can\'t connect to server: %s' % e)
        LOG.error(traceback.format_exc())
        return
    for line in log_out[0].splitlines():
        ignore = False
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
            LOG.debug('Check ignore error word in error line: %s' % error)
            if error in line:
                LOG.debug('Ignore this error line: %s' % line)
                ignore = True
        if ignore:
            continue

        if log_level == 'ERROR':
            LOG.error('Found ERROR in scalarizr_debug.log:\n %s' % line)
            raise ScalarizrLogError('Error in scalarizr_debug.log on server %s\nErrors: %s' % (node.id, log_out[0]))


@world.absorb
def wait_server_bootstrapping(role=None, status=ServerStatus.RUNNING, timeout=2100, server=None):
    """
    Wait a moment when new server starting in the pointed role and wait server will in selected state.
    Moreover this function remember all previous started servers.

    :param class:Role role: Show in which role lookup a new server
    :return class:Server: Return a new Server
    """
    status = ServerStatus.from_code(status)

    LOG.info('Launch process looking for new server in farm %s for role %s, wait status %s' %
             (world.farm.id, role, status))

    previous_servers = getattr(world, '_previous_servers', [])
    if not previous_servers:
        world._previous_servers = previous_servers

    LOG.debug('Previous servers: %s' % previous_servers)

    lookup_server = server or None
    lookup_node = None

    start_time = time.time()

    while time.time() - start_time < timeout:
        if not lookup_server:
            LOG.debug('Reload servers in role')
            if not role:
                world.farm.servers.reload()
                servers = world.farm.servers
            else:
                role.servers.reload()
                servers = role.servers
            for server in servers:
                LOG.debug('Work with server: %s - %s' % (server.id, server.status))
                if not server in previous_servers and server.status in [ServerStatus.PENDING_LAUNCH,
                                                                        ServerStatus.PENDING,
                                                                        ServerStatus.INIT,
                                                                        ServerStatus.RUNNING]:
                    LOG.debug('I found a server: %s' % server.id)
                    lookup_server = server
        if lookup_server:
            LOG.debug('Reload lookup_server')
            previous_state = lookup_server.status
            lookup_server.reload()

            LOG.debug('Check lookup server terminated?')
            if lookup_server.status in [ServerStatus.TERMINATED, ServerStatus.PENDING_TERMINATE] \
                and not status in [ServerStatus.TERMINATED, ServerStatus.PENDING_TERMINATE]:
                raise ServerTerminated('Server %s change status to %s (was %s)' %
                                       (lookup_server.id, lookup_server.status, previous_state))

            LOG.debug('Check lookup server launch failed')
            if lookup_server.is_launch_failed:
                raise ServerFailed('Server %s failed in %s. Reason: %s'
                                   % (lookup_server.id, ServerStatus.PENDING_LAUNCH,
                                      lookup_server.get_failed_status_message()))

            LOG.debug('Check lookup server init failed')
            if lookup_server.is_init_failed:
                raise ServerFailed('Server %s failed in %s. Failed (Why?): %s' %
                                   (lookup_server.id, ServerStatus.INIT, lookup_server.get_failed_status_message()))

            LOG.debug('Try get node')
            if not lookup_node and not lookup_server.status in [ServerStatus.PENDING_LAUNCH,
                                                                ServerStatus.PENDING_TERMINATE,
                                                                ServerStatus.TERMINATED,
                                                                ServerStatus.PENDING_SUSPEND,
                                                                ServerStatus.SUSPENDED]:
                LOG.debug('Try to get node object for lookup server')
                lookup_node = world.cloud.get_node(lookup_server)

            LOG.debug('Verify debug log in node')
            if lookup_node and not lookup_server.status in [ServerStatus.PENDING_LAUNCH,
                                                            ServerStatus.PENDING_TERMINATE,
                                                            ServerStatus.TERMINATED,
                                                            ServerStatus.PENDING_SUSPEND,
                                                            ServerStatus.SUSPENDED]:
                if not Dist.is_windows_family(lookup_server.role.dist):
                    LOG.debug('Check scalarizr log in lookup server')
                    verify_scalarizr_log(lookup_node)

            LOG.debug('If server Running and we wait Initializing, return server')
            if status == ServerStatus.INIT and lookup_server.status == ServerStatus.RUNNING:
                LOG.info('We wait Initializing but server already Running')
                status = ServerStatus.RUNNING

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
            raise TimeoutError('Server %s not in state "%s" it has status: "%s"'
                               % (lookup_server.id, status, lookup_server.status))
        raise TimeoutError('New server in role "%s" was not founding' % role)



@world.absorb
def wait_servers_running(role, count):
    role.servers.reload()
    previous_servers = getattr(world, '_previous_servers', [])
    run_count = 0
    for server in role.servers:
        if server.status == ServerStatus.RUNNING:
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
    world.farm.servers.reload()
    for server in world.farm.servers:
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
        last_internal_message = getattr(world, '_server_%s_last_message' % server.id, None)
        for message in server.messages:
            LOG.debug('Work with message: %s / %s - %s (%s) on server %s ' %
                      (message.type, message.name, message.delivered, int(message.id), server.id))
            if last_internal_message and int(message.id) <= int(last_internal_message.id):
                LOG.debug('This message <= when last internal message: %s <= %s' % (int(message.id), int(last_internal_message.id)))
                continue
            if message.name == message_name and message.type == message_type:
                LOG.info('This message matching the our pattern')
                if message.delivered:
                    LOG.info('Lookup message delivered')
                    setattr(world, '_server_%s_last_message' % server.id, message)
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
            LOG.debug('Delivered servers = %s, servers = %s' % (delivered_servers, servers))
            if delivered_servers == servers:
                LOG.info('All servers (%s) has delivered message: %s / %s' % (servers, message_type, message_name))
                return True
            LOG.debug('Find message in all servers')
            for serv in servers:
                if serv in delivered_servers:
                    continue
                result = check_message_in_server(serv, message_name, message_type)
                if result:
                    LOG.info('Message %s delivered in server %s (in mass delivering mode)' % (message_name, serv.id))
                    delivered_servers.append(serv)
                    LOG.debug('Message delivered to servers: %s' % [s.id for s in delivered_servers])
        time.sleep(5)
    else:
        raise MessageNotFounded('%s / %s was not finding in servers: %s' % (message_type,
                                                                            message_name,
                                                                            [s.id for s in servers]))


@world.absorb
def wait_script_execute(server, message, state):
    #TODO: Rewrite this as expect server bootstrapping
    LOG.info('Find message %s and state %s in scripting logs' % (message, state))
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        if message in log.message and state == log.event:
            return True
    return False


@world.absorb
def get_hostname(server):
    serv = world.cloud.get_node(server)
    for i in range(3):
        out = serv.run('/bin/hostname')
        if out[0].strip():
            return out[0].strip()
        time.sleep(5)
    raise AssertionError('Can\'t get hostname from server: %s' % server.id)


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
        LOG.debug('Upload index page %s to server %s' % (name, n.id))
        n.run('mkdir /var/www/%s' % name)
        n.put_file(path='/var/www/%s/index.php' % name, content=index)
    for i in range(10):
        LOG.info('Try get index from URL: %s, attempt %s ' % (url, i+1))
        try:
            resp = requests.get(url, timeout=30, verify=False)
            break
        except Exception, e:
            LOG.warning("Error in openning page '%s': %s" % (url, e))
            time.sleep(15)
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
def check_text_in_scalarizr_log(node, text):
    out = node.run("cat /var/log/scalarizr_debug.log | grep '%s'" % text)[0]
    if text in out:
        return True
    return False


@world.absorb
def set_iptables_rule(server, port):
    """Insert iptables rule in the top of the list (str, str, list||tuple)->"""
    LOG.info('Insert iptables rule to server %s for opening port %s' % (server, port))
    node = world.cloud.get_node(server)
    my_ip = world.get_external_local_ip()
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
def change_service_status(server, service, status, use_api=False, change_pid=False):
    """change_service_status(status, service, server) Change process status on remote host by his name
    Return pid before change status, pid after change status, exit code

    :type   status: str
    :param  status: Service status start, stop, restart, etc or api methods service_restart

    :type   service: dict
    :param  service: {node: name, api: name}, Service node name - scalarizr, apache2, etc...,
                     service api endpoint name apache, etc...

    :type   server: obj
    :param  server: Server object

    :type   use_api:   bool
    :param  use_api:   Status is api call or node command

    :type   change_pid:   bool
    :param  change_pid:   Status is changed pid for node service
    """
    #Init params
    node = world.cloud.get_node(server)

    #Change process status by calling api method or service command
    def change_status():
        if use_api:
            api = SzrApiServiceProxy(server.public_ip, str(server.details['scalarizr.key']))
            #Change process status by calling api call
            try:
                return getattr(getattr(api, service['api']), status)()
            except Exception as e:
                error_msg = """An error occurred while trying to execute a command %(command)s.
                               Original error: %(error)s""" % {
                    'error': e,
                    'command': '%s.%s()' % (service['api'], status)
                }
                LOG.error(error_msg)
                raise Exception(error_msg)
        else:
            #Change process status by  calling command service
            return node.run("service %(process)s %(status)s && sleep 5" %
                            {'process': service['node'], 'status': status})

    #Get process pid
    def get_pid():
        return node.run("pgrep -l %(process)s | awk {print'$1'} && sleep 5" %
                        {'process': service['node']})[0].rstrip('\n').split('\n')

    #Change status and get pid
    return {
        'pid_before': get_pid() if change_pid else [''],
        'info': change_status(),
        'pid_after': get_pid()
    }

@world.absorb
def is_log_rotate(server, process, rights, group=None):
    """Checks for logrotate config file and rotates the log. Returns the status of the operation."""
    if not group:
        group = ['nogroup', process]
    elif isinstance(group, str):
        group = [group, process]
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
                                    log_file_atr['group'] in group):
                        raise AssertionError("%(file)s file attributes are not correct. Wrong attributes %(atr)s: " %
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
