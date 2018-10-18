import copy
import logging
import re
import time
import traceback
import typing as tp
from datetime import datetime
from distutils.util import strtobool

from revizor2 import CONF
from revizor2.api import Farm, Role, Server, Message, Script
from revizor2.cloud import Cloud, ExtendedNode
from revizor2.consts import ServerStatus, Dist, Platform, MessageStatus
from revizor2.exceptions import ServerTerminated, \
    ServerFailed, TimeoutError, MessageNotFounded, MessageFailed, ScalarizrLogError
from revizor2.utils import DictToObj, wait_until

LOG = logging.getLogger(__name__)

SCALARIZR_LOG_IGNORE_ERRORS = [
    'boto',
    'p2p_message',
    'Caught exception reading instance data',
    'Expected list, got null. Selector: listvolumesresponse',
    'error was thrown due to the hostname format',
    "HTTPSConnectionPool(host='my.scalr.com', port=443): Max retries exceeded",
    "Error synchronizing server time: Unable to synchronize time, cause ntpdate binary is not found in $PATH"
]


def wait_status(context: dict,
                cloud: Cloud,
                farm: Farm,
                role: Role = None,
                status: str = ServerStatus.RUNNING,
                timeout: int = 2100,
                server: Server = None):
    platform = CONF.feature.platform
    status = ServerStatus.from_code(status)

    LOG.info(f'Launch process looking for new server in farm {farm.id} for role {role}, wait status {status}')

    previous_servers = context.get('_previous_servers', [])
    if not previous_servers:
        context['_previous_servers'] = previous_servers

    LOG.debug(f'Previous servers: {previous_servers}')

    lookup_server = server or None
    lookup_node = None
    azure_failed = 0

    start_time = time.time()

    while time.time() - start_time < timeout:
        if not lookup_server:
            LOG.debug('Reload servers in role')
            if not role:
                farm.servers.reload()
                servers = farm.servers
            else:
                role.servers.reload()
                servers = role.servers
            for server in servers:
                LOG.debug(f'Work with server: {server.id} - {server.status}')
                if server not in previous_servers and server.status in [ServerStatus.PENDING_LAUNCH,
                                                                        ServerStatus.PENDING,
                                                                        ServerStatus.INIT,
                                                                        ServerStatus.RUNNING]:
                    LOG.debug(f'I found a server: {server.id}')
                    lookup_server = server
        if lookup_server:
            LOG.debug('Reload lookup_server')
            previous_state = lookup_server.status
            lookup_server.reload()

            LOG.debug('Check lookup server terminated?')
            if lookup_server.status in [ServerStatus.TERMINATED,
                                        ServerStatus.PENDING_TERMINATE,
                                        ServerStatus.MISSING] \
                    and status not in [ServerStatus.TERMINATED,
                                       ServerStatus.PENDING_TERMINATE,
                                       ServerStatus.MISSING]:
                raise ServerTerminated(f'Server {lookup_server.id} change status to {lookup_server.status} '
                                       f'(was {previous_state})')

            LOG.debug('Check lookup server launch failed')
            if lookup_server.is_launch_failed:
                err_msg = (
                    'Can not decode json response data',
                    'Cannot establish connection with CloudStack server. (Server returned nothing )'
                )
                failed_message = lookup_server.get_failed_status_message()
                if platform.is_cloudstack and any(msg in failed_message for msg in err_msg):
                    time.sleep(90)
                    lookup_server = None
                    lookup_node = None
                    continue
                # if platform.is_azure and azure_failed != 2:
                #     LOG.warning('Server %s in Azure and failed %s attempt with message: "%s"' % (
                #         lookup_server.id,
                #         azure_failed + 1,
                #         lookup_server.get_failed_status_message()))
                #     azure_failed += 1
                #     time.sleep(15)
                #     continue
                if status == ServerStatus.FAILED:
                    LOG.debug('Return server because we wait a failed state')
                    return lookup_server
                raise ServerFailed(f'Server {lookup_server.id} failed in {ServerStatus.PENDING_LAUNCH}. '
                                   f'Reason: {failed_message}')

            LOG.debug('Check lookup server init failed')
            if lookup_server.is_init_failed:
                if status == ServerStatus.FAILED:
                    LOG.debug('Return server because we wait a failed state')
                    return lookup_server
                raise ServerFailed(f'Server {lookup_server.id} failed in {ServerStatus.INIT}. Failed (Why?): '
                                   f'{lookup_server.get_failed_status_message()}')

            LOG.debug('Try get node')
            if not lookup_node and lookup_server.status not in [ServerStatus.PENDING_LAUNCH,
                                                                ServerStatus.PENDING_TERMINATE,
                                                                ServerStatus.TERMINATED,
                                                                ServerStatus.PENDING_SUSPEND,
                                                                ServerStatus.SUSPENDED] \
                    and status != ServerStatus.PENDING:
                LOG.debug('Try to get node object for lookup server')
                lookup_node = cloud.get_node(lookup_server)

            LOG.debug('Verify update log in node')
            if lookup_node and lookup_server.status == ServerStatus.PENDING and status != ServerStatus.PENDING:
                LOG.debug('Check scalarizr update log in lookup server')
                if not Dist(lookup_server.role.dist).is_windows and not platform.is_azure:
                    # TODO: verify_scalarizr_log(lookup_node, log_type='update')
                    pass
                else:
                    if platform != Platform.RACKSPACENGUS:
                        # TODO: verify_scalarizr_log(lookup_node, log_type='update', windows=True,
                        # server=lookup_server)
                        pass

            LOG.debug('Verify debug log in node')
            if lookup_node and lookup_server.status not in [ServerStatus.PENDING_LAUNCH,
                                                            ServerStatus.PENDING_TERMINATE,
                                                            ServerStatus.TERMINATED,
                                                            ServerStatus.PENDING_SUSPEND,
                                                            ServerStatus.SUSPENDED] \
                    and not status == ServerStatus.FAILED:
                LOG.debug('Check scalarizr debug log in lookup server')
                if not Dist(lookup_server.role.dist).is_windows and not platform.is_azure:
                    # TODO: verify_scalarizr_log(lookup_node)
                    pass
                else:
                    # TODO: verify_scalarizr_log(lookup_node, windows=True, server=lookup_server)
                    pass

            LOG.debug('If server Running and we wait Initializing, return server')
            if status == ServerStatus.INIT and lookup_server.status == ServerStatus.RUNNING:
                LOG.info('We wait Initializing but server already Running')
                status = ServerStatus.RUNNING
            if status == ServerStatus.RESUMING and lookup_server.status == ServerStatus.RUNNING:
                LOG.info('We wait Resuming but server already Running')
                status = ServerStatus.RUNNING

            LOG.debug(f'Compare server status "{lookup_server.status}" == "{status}"')
            if lookup_server.status == status:
                LOG.info(f'Lookup server in right status now: {lookup_server.status}')
                if status == ServerStatus.RUNNING:
                    lookup_server.messages.reload()
                    if platform.is_azure \
                            and not Dist(lookup_server.role.dist).is_windows \
                            and not ('ResumeComplete' in map(lambda m: m.name, lookup_server.messages)) \
                            and lookup_server.is_scalarized:
                        LOG.debug(f'Wait update ssh authorized keys on azure {lookup_server.id} server')
                        # TODO: wait_server_message(
                        #     lookup_server,
                        #     'UpdateSshAuthorizedKeys',
                        #     timeout=2400)
                    LOG.debug('Insert server to previous servers')
                    previous_servers.append(lookup_server)
                LOG.debug(f'Return server {lookup_server}')
                return lookup_server
        LOG.debug('Sleep 10 seconds')
        time.sleep(10)
    else:
        if lookup_server:
            raise TimeoutError(f'Server {lookup_server.id} not in state "{status}" '
                               f'it has status: "{lookup_server.status}"')
        raise TimeoutError(f'New server in role "{role}" was not founding')


def get_hostname_by_server_format(server: Server) -> str:
    return f'r{server.farm_id}-{server.farm_role_id}-{server.index}'


def get_iptables_rules(cloud: Cloud, server: Server) -> str:
    return cloud.get_node(server).run('iptables -L').std_out


def get_incoming_messages(server: Server, msg: str) -> tp.List[Message]:
    server.messages.reload()
    return [m for m in server.messages if m.type == 'in' and m.name == msg]


def get_szr_messages(node: ExtendedNode, convert: bool = False):
    LOG.info('Get messages list from server %s' % node.id)
    cmd = '/opt/bin/szradm list-messages' if CONF.feature.dist.id == 'coreos' else 'szradm list-messages'
    out = node.run(cmd)

    if out.std_out.strip() == '':
        return []
    lines = out.std_out.splitlines()
    # remove horizontal borders
    lines = filter(lambda x: not x.startswith('+'), lines)

    # split each line

    def split_tline(line):
        return map(lambda x: x.strip('| '), line.split(' | '))

    lines = list(map(split_tline, lines))
    # get column names
    column_names = lines.pop(0)
    # remove special chars in the end of head
    head = list(map(lambda name: re.split(r'([\_\-\+\?\!])$', name)[0], column_names))

    # [{column_name: value}]
    messages = [dict(zip(head, line)) for line in lines]
    if convert:
        messages = list(map(lambda m: DictToObj(m), messages))

    LOG.info('Server messages: %s' % messages)
    return messages


def execute_state_action(server: Server, action: str, reboot_type: str = None):
    LOG.info('%s server %s' % (action.capitalize(), server.id))
    args = {'method': reboot_type.strip() if reboot_type else 'soft'}
    meth = getattr(server, action)
    res = meth(**args) if action == 'reboot' else meth()
    error_message = None
    if isinstance(res, bool) and not res:
        error_message = "% success: %s" % (action, res)
    elif isinstance(res, dict):
        error_message = res.get('errorMessage', None)
    # Workaround for SCALRCORE-1576
    if error_message == ['Unable to perform request to scalarizr: A server error occurred.'
                         '  Please contact the administrator. (500)']:
        error_message = None
    assert not error_message, error_message
    LOG.info('Server %s was %sed' % (server.id, action))


def wait_unstored_message(cloud: Cloud, servers: tp.Union[Server, tp.List[Server]],
                          message_name: str, message_type: str = 'out',
                          find_in_all: bool = False,
                          timeout: int = 1000):
    if not isinstance(servers, (list, tuple)):
        servers = [servers]
    delivered_to = []
    server_messages = {}
    message_type = 'in' if message_type.strip() not in ('sends', 'out') else 'out'
    start_time = time.time()
    while time.time() - start_time < timeout:
        if delivered_to == servers:
            LOG.info('All servers has message: %s / %s' % (message_type, message_name))
            break
        for server in servers:
            if server in delivered_to:
                continue
            LOG.info('Searching message "%s/%s" on %s node' % (message_type, message_name, server.id))
            node = cloud.get_node(server)
            lookup_messages = server_messages.setdefault(server.id, [])
            node_messages = reversed(get_szr_messages(node, convert=True))
            message = list(filter(lambda m:
                                  m.name == message_name
                                  and m.direction == message_type
                                  and m.id not in lookup_messages
                                  and strtobool(m.handled), node_messages))

            if message:
                LOG.info('Message found: %s' % message[0].id)
                lookup_messages.append(message[0].id)
                if find_in_all:
                    LOG.info('Message %s delivered to the server %s' % (message_name, server.id))
                    delivered_to.append(server)
                    continue
                return server
        time.sleep(30)
    else:
        raise MessageNotFounded('%s/%s was not finding' % (message_type, message_name))


def wait_server_message(servers: tp.Union[Server, tp.List[Server]],
                        message_name: str, message_type: str = 'out',
                        find_in_all: bool = False,
                        timeout: int = 600):
    """
    Wait message in server list (or one server). If find_in_all is True, wait this message in all
    servers.
    """
    server_messages = {}

    def check_message_in_server(srv: Server):
        srv.messages.reload()
        lookup_messages = server_messages.setdefault(srv.id, [])
        for message in reversed(srv.messages):
            LOG.debug('Work with message: %s / %s - %s (%s) on server %s ' %
                      (message.type, message.name, message.delivered, message.id, srv.id))
            if message.id in lookup_messages:
                LOG.debug('Message %s was already lookuped' % message.id)
                continue
            if message.name == message_name and message.type == message_type:
                LOG.info('This message matching the our pattern')
                if message.delivered:
                    LOG.info('Lookup message delivered')
                    lookup_messages.append(message.id)
                    return True
                elif message.status == MessageStatus.FAILED:
                    lookup_messages.append(message.id)
                    raise MessageFailed('Message %s / %s (%s) failed' % (message.type, message.name, message.id))
                elif message.status == MessageStatus.UNSUPPORTED:
                    raise MessageFailed('Message %s / %s (%s) unsupported' % (message.type, message.name, message.id))
        return False

    message_type = 'in' if message_type.strip() not in ('sends', 'out') else 'out'
    if not isinstance(servers, (list, tuple)):
        servers = [servers]
    LOG.info('Try found message %s / %s in servers %s' % (message_type, message_name, servers))
    start_time = time.time()
    delivered_servers = []
    while time.time() - start_time < timeout:
        if not find_in_all:
            for serv in servers:
                if check_message_in_server(serv):
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
                result = check_message_in_server(serv)
                if result:
                    LOG.info('Message %s delivered in server %s (in mass delivering mode)' % (message_name, serv.id))
                    delivered_servers.append(serv)
                    LOG.debug('Message delivered to servers: %s' % [s.id for s in delivered_servers])
        time.sleep(5)
    else:
        raise MessageNotFounded('%s / %s was not finding in servers: %s' % (message_type,
                                                                            message_name,
                                                                            [s.id for s in servers]))


def validate_server_message(cloud: Cloud, farm: Farm, msgtype: str, msg: str, server: Server = None,
                            failed: bool = False, unstored_message: bool = False, timeout: int = 1500):
    """Check scalr in/out message delivering"""
    if not server:  # Check messages for all running servers
        LOG.info('Check message %s %s in all servers' % (msg, msgtype))
        farm.servers.reload()
        servers = [serv for serv in farm.servers if serv.status == ServerStatus.RUNNING]
        if unstored_message:
            wait_unstored_message(cloud, servers, msg.strip(), msgtype, find_in_all=True, timeout=timeout)
        else:
            wait_server_message(servers, msg.strip(), msgtype, find_in_all=True, timeout=timeout)
    else:
        LOG.info('Wait message %s / %s in server: %s' % (msgtype, msg.strip(), server.id))
        if msg == 'VhostReconfigure' and CONF.feature.platform.is_ec2 and failed:
            server.logs.reload()
            for log in server.logs:
                if msg in log.message:
                    return
            raise MessageNotFounded("%s was not found in %s system logs!" % (msg, server.id))
        try:
            if unstored_message:
                wait_unstored_message(cloud, server, msg.strip(), msgtype, timeout=timeout)
            else:
                wait_server_message(server, msg.strip(), msgtype, timeout=timeout)
        except MessageFailed:
            if not failed:
                raise


def execute_script(context: dict, farm: Farm, server: Server, script_name: str,
                   is_local: bool = False, synchronous: bool = False):
    path = None
    if is_local:
        path = script_name
        script_id = None
    else:
        script_id = Script.get_id(script_name)
    LOG.info('Execute script "%s" with id: %s' % (script_name, script_id))
    server.scriptlogs.reload()
    context['_server_%s_last_scripts' % server.id] = copy.deepcopy(server.scriptlogs)
    context['_server_%s_last_script_name' % server.id] = script_name
    Script.script_execute(farm.id, server.farm_role_id, server.id, script_id, int(synchronous), path=path)
    LOG.info('Script executed success')


def validate_last_script_result(context: dict,
                                cloud: Cloud,
                                server: Server,
                                name: str = None,
                                event: str = None,
                                user: str = None,
                                log_contains: str = None,
                                std_err: bool = False,
                                exitcode: int = None,
                                new_only: bool = False,
                                timeout: int = 600):
    """Verifies that server scripting log contains info about script execution."""
    out_name = 'STDERR' if std_err else 'STDOUT'
    LOG.debug('Checking scripting %s logs on %s by parameters:\n'
              '  script name:\t"%s"\n'
              '  event:\t\t%s\n'
              '  user:\t\t%s\n'
              '  log_contains:\t%s\n'
              '  exitcode:\t%s\n'
              '  new_only:\t%s\n'
              '  timeout:\t%s'
              % (out_name,
                 server.id,
                 name or 'Any',
                 event or 'Any',
                 user or 'Any',
                 log_contains or 'Any',
                 exitcode or 'Any',
                 new_only,
                 timeout))

    contain = log_contains.split(';') if log_contains else []
    last_scripts = context['_server_%s_last_scripts' % server.id] if new_only else []
    # Convert script name, because scalr converts name to:
    # substr(preg_replace("/[^A-Za-z0-9]+/", "_", $script->name), 0, 50)
    if name:
        name = re.sub('[^A-Za-z0-9/.:]+', '_', name)[:50]
        if not name.startswith('http') and not name.startswith('/'):
            name = name.replace('.', '')
    timeout //= 10

    for _ in range(timeout + 1):
        server.scriptlogs.reload()
        for log in server.scriptlogs:
            LOG.debug('Checking script log:\n'
                      '  name:\t"%s"\n'
                      '  event:\t"%s"\n'
                      '  run as:\t"%s"\n'
                      '  exitcode:\t"%s"'
                      % (log.name, log.event, log.run_as, log.exitcode))
            if log in last_scripts:
                LOG.debug('Pass this log because it in last scripts')
                continue
            if log.run_as is None:
                log.run_as = 'Administrator' if CONF.feature.dist.is_windows else 'root'
            event_matched = event is None or (log.event and log.event.strip() == event.strip())
            user_matched = user is None or (log.run_as == user)
            name_matched = name is None \
                           or (name == 'chef' and log.name.strip().startswith(name)) \
                           or (name.startswith('http') and log.name.strip().startswith(name)) \
                           or (name.startswith('local') and log.name.strip().startswith(name)) \
                           or log.name.strip() == name
            LOG.debug('Script matched parameters: event - %s, user - %s, name - %s' % (
                event_matched, user_matched, name_matched))
            if name_matched and event_matched and user_matched:
                LOG.debug('Script log matched search parameters')
                if exitcode is None or log.exitcode == exitcode:
                    # script exitcode is valid, now check that log output contains wanted text
                    message = log.message.split('STDOUT:', 1)[int(not std_err)]
                    ui_message = True
                    LOG.debug('Log message %s output: %s' % (out_name, message))
                    for cond in contain:
                        cond = cond.strip()
                        html_cond = cond.replace('"', '&quot;').replace('>', '&gt;').strip()
                        LOG.debug('Check condition "%s" in log' % cond)
                        found = (html_cond in message) if ui_message else (cond in message)
                        if not found \
                                and not CONF.feature.dist.is_windows \
                                and 'Log file truncated. See the full log in' in message:
                            full_log_path = re.findall(r'Log file truncated.'
                                                       r' See the full log in ([.\w\d/-]+)', message)[0]
                            node = cloud.get_node(server)
                            message = node.run('cat %s' % full_log_path).std_out
                            ui_message = False
                            found = cond in message
                        if not found:
                            raise AssertionError('Script on event "%s" (%s) contain: "%s" but lookup: \'%s\''
                                                 % (event, user, message, cond))
                    LOG.debug('This event exitcode: %s' % log.exitcode)
                    return True
                else:
                    raise AssertionError('Script on event \'%s\' (%s) exit with code: %s but lookup: %s'
                                         % (event, user, log.exitcode, exitcode))
        time.sleep(10)

    raise AssertionError(
        'I\'m not see script on event \'%s\' (%s) in script logs for server %s' % (event, user, server.id))


def validate_string_in_file(cloud: Cloud, server: Server, file_path: str, value: str, invert: bool = False):
    LOG.info('Verify file "%s" in %s %s "%s"' % (file_path, server.id,
                                                 'does not contain' if invert else 'contains',
                                                 value))
    node = cloud.get_node(server)
    out = node.run('cat %s | grep %s' % (file_path, value)).std_out.strip()
    assert bool(out) ^ invert, \
        'File %s %s: %s. Result of grep: %s' % (file_path,
                                                'contains' if invert else 'does not contain',
                                                value, out)


def check_text_in_scalarizr_log(node: ExtendedNode, text: str):
    out = node.run('cat /var/log/scalarizr_debug.log | grep "%s"' % text).std_out
    if text in out:
        return True
    return False


def check_scalarizr_log_errors(cloud: Cloud, server: Server, log_type: str = None):
    """Check scalarizr log for errors"""
    log_type = log_type or 'debug'
    node = cloud.get_node(server)
    if CONF.feature.dist.is_windows:
        validate_scalarizr_log_errors(cloud, node, windows=True, server=server, log_type=log_type)
    else:
        validate_scalarizr_log_errors(cloud, node, log_type=log_type)


def validate_scalarizr_log_errors(cloud: Cloud, node: ExtendedNode, server: Server = None,
                                  log_type: str = None, windows: bool = False):
    LOG.info('Verify scalarizr log in server: %s' % node.id)
    if server:
        server.reload()
        if not server.public_ip:
            LOG.debug('Server has no public IP yet')
            return
    else:
        if isinstance(node, Server):
            node = cloud.get_node(node)
        if not node.public_ips or not node.public_ips[0]:
            LOG.debug('Node has no public IP yet')
            return
    try:
        if windows:
            log_out = node.run("findstr /n \"ERROR WARNING Traceback\" \"C:\Program Files\Scalarizr\\var\log\scalarizr_%s.log\"" % log_type)
            if 'FINDSTR: Cannot open' in log_out.std_err:
                log_out = node.run("findstr /n \"ERROR WARNING Traceback\" \"C:\opt\scalarizr\\var\log\scalarizr_%s.log\"" % log_type)
            log_out = log_out.std_out
            LOG.debug('Findstr result: %s' % log_out)
        else:
            log_out = (node.run('grep -n "\- ERROR \|\- WARNING \|Traceback" /var/log/scalarizr_%s.log' % log_type)).std_out
            LOG.debug('Grep result: %s' % log_out)
    except BaseException as e:
        LOG.error('Can\'t connect to server: %s' % e)
        LOG.error(traceback.format_exc())
        return

    lines = log_out.splitlines()
    for i, line in enumerate(lines):
        ignore = False
        LOG.debug('Verify line "%s" for errors' % line)
        log_date = None
        log_level = None
        line_number = -1
        now = datetime.now()
        try:
            line_number = int(line.split(':', 1)[0])
            line = line.split(':', 1)[1]
            log_date = datetime.strptime(line.split()[0], '%Y-%m-%d')
            log_level = line.strip().split()[3]
        except (ValueError, IndexError):
            pass

        if log_date:
            if not log_date.year == now.year or \
                    not log_date.month == now.month or \
                    not log_date.day == now.day:
                continue

        for error in SCALARIZR_LOG_IGNORE_ERRORS:
            LOG.debug('Check ignore error word in error line: %s' % error)
            if error in line:
                LOG.debug('Ignore this error line: %s' % line)
                ignore = True
                break
        if ignore:
            continue

        if log_level == 'ERROR':
            LOG.error('Found ERROR in scalarizr_%s.log:\n %s' % (log_type, line))
            raise ScalarizrLogError('Error in scalarizr_%s.log on server %s\nErrors: %s' % (log_type, node.id, log_out))

        if log_level == 'WARNING' and i < len(lines) - 1:
            if '%s:Traceback' % (line_number + 1) in lines[i+1]:
                LOG.error('Found WARNING with Traceback in scalarizr_%s.log:\n %s' % (log_type, line))
                raise ScalarizrLogError('Error in scalarizr_%s.log on server %s\nErrors: %s' % (log_type, node.id, log_out))


def wait_servers_state(farm: Farm, state):
    """Wait for state of all servers"""
    wait_until(farm_servers_state,
               args=(farm, state),
               timeout=1800,
               error_text=('Servers in farm have no status %s' % state))


def farm_servers_state(farm: Farm, state):
    farm.servers.reload()
    for server in farm.servers:
        if server.status == ServerStatus.from_code(state):
            LOG.info('Servers is in %s state' % state)
            continue
        else:
            return False
    return True
