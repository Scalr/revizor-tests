import logging
import time
from collections import abc

import requests

import scalarizr.lib.server as lib_server
from revizor2 import CONF
from revizor2.api import Cloud, Server
from revizor2.consts import SERVICES_PORTS_MAP, BEHAVIORS_ALIASES
from revizor2.defaults import DEFAULT_SERVICES_CONFIG
from revizor2.helpers.parsers import get_repo_url, parser_for_os_family
from revizor2.utils import wait_until
from scalarizr.lib.common import run_only_if

LOG = logging.getLogger(__name__)


class VerifyProcessWork:

    @staticmethod
    def verify(cloud: Cloud, server: Server, behavior: str = None, port: int = None) -> bool:
        if not behavior:
            behavior = server.role.behaviors[0]
        LOG.info('Verify %s behavior process work in server %s (on port: %s)' % (behavior, server.id, port))
        if hasattr(VerifyProcessWork, '_verify_%s' % behavior):
            return getattr(VerifyProcessWork, '_verify_%s' % behavior)(cloud, server, port)
        return True

    @staticmethod
    def _verify_process_running(cloud: Cloud, server: Server, process_name: str) -> bool:
        LOG.debug('Check process %s in running state on server %s' % (process_name, server.id))
        node = cloud.get_node(server)
        with node.remote_connection() as conn:
            for i in range(3):
                out = conn.run("ps -C %s -o pid=" % process_name)
                if not out.std_out.strip():
                    LOG.warning("Process %s don't work in server %s (attempt %s)" % (process_name, server.id, i))
                else:
                    LOG.info("Process %s work in server %s" % (process_name, server.id))
                    return True
                time.sleep(5)
            return False

    @staticmethod
    def _verify_app(cloud: Cloud, server: Server, port: int) -> bool:
        LOG.info('Verify apache (%s) work in server %s' % (port, server.id))
        node = cloud.get_node(server)
        results = [
            VerifyProcessWork._verify_process_running(cloud, server,
                                                      DEFAULT_SERVICES_CONFIG['app'][node.os.family]['service_name']),
            node.check_open_port(port)
        ]
        return all(results)

    @staticmethod
    def _verify_www(cloud: Cloud, server: Server, port: int) -> bool:
        LOG.info('Verify nginx (%s) work in server %s' % (port, server.id))
        node = cloud.get_node(server)
        results = [
            VerifyProcessWork._verify_process_running(cloud, server, 'nginx'),
            node.check_open_port(port)
        ]
        return all(results)

    @staticmethod
    def _verify_redis(cloud: Cloud, server: Server, port: int) -> bool:
        LOG.info('Verify redis-server (%s) work in server %s' % (port, server.id))
        node = cloud.get_node(server)
        results = [
            VerifyProcessWork._verify_process_running(cloud, server, 'redis-server'),
            node.check_open_port(port)
        ]
        LOG.debug('Redis-server verifying results: %s' % results)
        return all(results)

    @staticmethod
    def _verify_scalarizr(cloud: Cloud, server: Server, port: int = 8010) -> bool:
        LOG.info('Verify scalarizr (%s) work in server %s' % (port, server.id))
        node = cloud.get_node(server)
        if CONF.feature.platform.is_cloudstack and cloud._driver.use_port_forwarding():
            port = server.details['scalarizr.ctrl_port']
        results = [
            VerifyProcessWork._verify_process_running(cloud, server, 'scalarizr'),
            VerifyProcessWork._verify_process_running(cloud, server, 'scalr-upd-client'),
            node.check_open_port(port)
        ]
        LOG.debug('Scalarizr verifying results: %s' % results)
        return all(results)

    @staticmethod
    def _verify_memcached(cloud: Cloud, server: Server, port: int) -> bool:
        LOG.info('Verify memcached (%s) work in server %s' % (port, server.id))
        node = cloud.get_node(server)
        results = [
            VerifyProcessWork._verify_process_running(cloud, server, 'memcached'),
            node.check_open_port(port)
        ]
        return all(results)


def reboot_scalarizr(cloud: Cloud, server: Server):
    if CONF.feature.dist.is_systemd:
        cmd = "systemctl restart scalarizr"
    else:
        cmd = "/etc/init.d/scalarizr restart"
    node = cloud.get_node(server)
    node.run(cmd)
    LOG.info('Scalarizr restart complete')
    time.sleep(15)


def validate_scalarizr_log_contains(cloud: Cloud, server: Server, message: str):
    node = cloud.get_node(server)
    LOG.info('Check scalarizr log')
    wait_until(lib_server.check_text_in_scalarizr_log, timeout=300, args=(node, message),
               error_text='Not see %s in debug log' % message)


def execute_command(cloud: Cloud, server: Server, command: str):
    if (command.startswith('scalarizr') or command.startswith('szradm')) and CONF.feature.dist.id == 'coreos':
        command = '/opt/bin/' + command
    node = cloud.get_node(server)
    LOG.info('Execute command on server: %s' % command)
    node.run(command)


def get_scalaraizr_latest_version(branch: str) -> str:
    os_family = CONF.feature.dist.family
    index_url = get_repo_url(os_family, branch)
    LOG.debug('Check package from index_url: %s' % index_url)
    repo_data = parser_for_os_family(CONF.feature.dist.mask)(index_url=index_url)
    versions = [package['version'] for package in repo_data if
                package['name'] == 'scalarizr'] if os_family != 'coreos' else repo_data
    versions.sort(reverse=True)
    return versions[0]


def validate_scalarizr_version(server: Server, branch: str = None):
    """
    Argument branch can be system or role.
    System branch - CONF.feature.branch
    Role branch - CONF.feature.to_branch
    """
    if branch == 'system' or not branch:
        branch = CONF.feature.branch
    elif branch == 'role':
        branch = CONF.feature.to_branch
    if '.' in branch and branch.replace('.', '').isdigit():
        last_version = branch
    else:
        # Get custom repo url
        last_version = get_scalaraizr_latest_version(branch)
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
        except requests.exceptions.HTTPError:
            time.sleep(3)
    else:
        raise AssertionError('Can\'t get access to update client 5 times (15 seconds)')
    LOG.debug('Last scalarizr version from update client status: %s' % update_status['installed'])
    if not update_status['state'] == 'noop' and update_status['prev_state'] == 'completed':
        assert update_status['state'] == 'completed', \
            'Update client not in normal state. Status = "%s", Previous state = "%s"' % \
            (update_status['state'], update_status['prev_state'])
    assert last_version == installed_version, \
        'Server not has last build of scalarizr package, installed: %s last_version: %s' % \
        (installed_version, last_version)


@run_only_if(dist=['!coreos'])
def validate_service(cloud: Cloud, server: Server, service: str, closed: bool = False):
    # FIXME: Rewrite this ugly logic
    port = SERVICES_PORTS_MAP[service]
    if isinstance(port, abc.Sequence):
        port = port[0]
    LOG.info('Verify port %s is %s on server %s' % (
        port, 'closed' if closed else 'open', server.id
    ))
    if service == 'scalarizr' and CONF.feature.dist.is_windows:
        status = None
        for _ in range(5):
            status = server.upd_api.status()['service_status']
            if status == 'running':
                return
            time.sleep(5)
        else:
            raise AssertionError('Scalarizr is not running in windows, status: %s' % status)
    node = cloud.get_node(server)
    if not CONF.feature.dist.is_windows:
        lib_server.set_iptables_rule(cloud, server, port)
    if CONF.feature.platform.is_cloudstack and cloud._driver.use_port_forwarding():
        # TODO: Change login on this behavior
        port = cloud.open_port(node, port, ip=server.public_ip)
    if service in BEHAVIORS_ALIASES.values():
        behavior = [x[0] for x in BEHAVIORS_ALIASES.items() if service in x][0]
    else:
        behavior = service
    check_result = VerifyProcessWork.verify(cloud, server, behavior, port)
    if closed and check_result:
        raise AssertionError("Service %s must be don't work but it work!" % service)
    if not closed and not check_result:
        raise AssertionError("Service %s must be work but it doesn't work! (results: %s)" % (service, check_result))
