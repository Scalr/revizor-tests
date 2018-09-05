import logging
import time
import typing as tp

from revizor2 import CONF
from revizor2.api import Farm, Role, Server, Message
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Dist, Platform
from revizor2.exceptions import ServerTerminated, \
    ServerFailed, TimeoutError

LOG = logging.getLogger(__name__)


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
