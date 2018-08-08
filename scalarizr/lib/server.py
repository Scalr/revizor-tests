import logging
import time
from typing import List

from revizor2 import CONF
from revizor2.api import Farm, Role, Server
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Dist, Platform
from revizor2.exceptions import ServerTerminated, \
    ServerFailed, TimeoutError
from revizor2.helpers.parsers import parser_for_os_family, get_repo_url

LOG = logging.getLogger(__name__)


def wait_status(context: dict,
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
                lookup_node = context['cloud'].get_node(lookup_server)

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


def assert_scalarizr_version(server: Server, branch: str = None):
    """
    Argument branch can be system or role.
    System branch - CONF.feature.branch
    Role branch - CONF.feature.to_branch
    """
    # FIXME: Rewrite this ugly code!
    if branch == 'system' or not branch:
        branch = CONF.feature.branch
    elif branch == 'role':
        branch = CONF.feature.to_branch
    os_family = Dist(server.role.dist).family
    # if branch == 'latest' and 'base' in server.role.behaviors:
    #     branch = DEFAULT_PY3_BRANCH
    if '.' in branch and branch.replace('.', '').isdigit():
        last_version = branch
    else:
        # Get custom repo url
        index_url = get_repo_url(os_family, branch)
        LOG.debug('Check package from index_url: %s' % index_url)
        repo_data = parser_for_os_family(server.role.dist)(index_url=index_url)
        versions = [package['version'] for package in repo_data if
                    package['name'] == 'scalarizr'] if os_family != 'coreos' else repo_data
        versions.sort(reverse=True)
        last_version = versions[0]
        if last_version.strip().endswith('-1'):
            last_version = last_version.strip()[:-2]
    LOG.debug('Last scalarizr version %s for branch %s' % (last_version, branch))
    # Get installed scalarizr version
    for _ in range(10):
        try:
            update_status = server.upd_api.status(cached=False)
            installed_version = update_status['installed']
            if installed_version.strip().endswith('-1'):
                installed_version = installed_version.strip()[:-2]
            break
        except Exception:
            time.sleep(3)
    else:
        raise AssertionError('Can\'t get access to update client 5 times (15 seconds)')
    LOG.debug('Last scalarizr version from update client status: %s' % update_status['installed'])
    if not update_status['state'] == 'noop' and update_status['prev_state'] == 'completed':
        assert update_status['state'] == 'completed', \
            'Update client not in normal state. Status = "%s", Previous state = "%s"' % \
            (update_status['state'], update_status['prev_state'])
    assert last_version == installed_version, \
        'Server not has last build of scalarizr package, installed: %s last_version: %s' % (
        installed_version, last_version)


def verify_hostname_is_valid(server: Server):
    hostname = server.api.system.get_hostname()
    valid_hostname = get_hostname_by_server_format(server)
    assert hostname.lower() == valid_hostname.lower(), \
        f'Hostname in server {server.id} is not valid: {hostname} ({valid_hostname})'


def get_hostname_by_server_format(server: Server):
    return f'r{server.farm_id}-{server.farm_role_id}-{server.index}'


# @world.run_only_if(platform=['!%s' % Platform.RACKSPACENGUS, '!%s' % Platform.CLOUDSTACK],
#     dist=['!scientific6', '!centos-6-x', '!centos-7-x', '!coreos']) <-- TODO
def verify_ports_in_iptables(cloud: Cloud, server: Server, ports: List[int], invert: bool = False):
    LOG.info(f'Verify ports {ports} in iptables')
    if CONF.feature.platform.is_cloudstack:
        LOG.info('Not check iptables because CloudStack')
        return
    node = cloud.get_node(server)
    iptables_rules = node.run('iptables -L').std_out
    LOG.debug(f'iptables rules:\n{iptables_rules}')
    for port in ports:
        LOG.debug(f'Check port "{port}" in iptables rules')
        if str(port) in iptables_rules and invert:
            raise AssertionError('Port "%s" in iptables rules!' % port)
        elif not invert and str(port) not in iptables_rules:
            raise AssertionError('Port "%s" is NOT in iptables rules!' % port)


def run_cmd_command(server: Server, command: str, raise_exc: bool = True):
    console = get_windows_session(server)
    LOG.info('Run command: %s in server %s' % (command, server.id))
    out = console.run_cmd(command)
    LOG.debug('Result of command: %s\n%s' % (out.std_out, out.std_err))
    if not out.status_code == 0 and raise_exc:
        raise AssertionError('Command: "%s" exit with status code: %s and stdout: %s\n stderr:%s' % (
        command, out.status_code, out.std_out, out.std_err))
    return out


def get_windows_session(server: Server = None, public_ip: str = None, password: str = None, timeout: int = None):
    platform = CONF.feature.platform
    time_until = time.time() + timeout if timeout else None
    username = 'Administrator'
    port = 5985
    while True:
        try:
            if server:
                server.reload()
                public_ip = server.public_ip
                password = password or server.windows_password
                if not password:
                    password = 'Scalrtest123'
            if platform.is_gce or platform.is_azure:
                username = 'scalr'
            elif platform.is_cloudstack and world.cloud._driver.use_port_forwarding():
                node = world.cloud.get_node(server)
                port = world.cloud.open_port(node, port)
            LOG.info('Used credentials for windows session: %s:%s %s:%s' % (public_ip, port, username, password))
            session = winrm.Session(
                'http://%s:%s/wsman' % (public_ip, port),
                auth=(username, password))
            LOG.debug('WinRm instance: %s' % session)
            return session
        except Exception as e:
            LOG.error('Got windows session error: %s' % e.message)
        if time.time() >= time_until:
            raise TimeoutError
        time.sleep(5)
