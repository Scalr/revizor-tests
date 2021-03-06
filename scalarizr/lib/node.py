import time
import logging
from collections import abc
from datetime import datetime

import requests
from libcloud.compute.base import NodeImage
from libcloud.compute.types import NodeState

from revizor2 import CONF
from revizor2.utils import wait_until
from revizor2.api import Cloud, Server, IMPL
from revizor2.cloud.node import ExtendedNode, Response
from revizor2.consts import SERVICES_PORTS_MAP, BEHAVIORS_ALIASES, Dist
from revizor2.defaults import DEFAULT_SERVICES_CONFIG
from revizor2.helpers.parsers import get_repo_url, parser_for_os_family

import scalarizr.lib.server as lib_server


LOG = logging.getLogger(__name__)

PS_RUN_AS = '''powershell -NoProfile -ExecutionPolicy Bypass -Command "{command}"'''  # TODO: Move this to Cloud.Node??


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
    node = cloud.get_node(server)

    if CONF.feature.dist.is_windows:
        node.run('Restart-Service Scalarizr -Force')
    else:
        if CONF.feature.dist.is_systemd:
            cmd = "systemctl restart scalarizr"
        else:
            cmd = "/etc/init.d/scalarizr restart"
        node.run(cmd)
    LOG.info('Scalarizr restart complete')
    time.sleep(15)


def assert_scalarizr_log_contains(cloud: Cloud, server: Server, message: str):
    node = cloud.get_node(server)
    LOG.info('Check scalarizr log')
    wait_until(lib_server.check_text_in_scalarizr_log, timeout=300, args=(node, message),
               error_text='Not see %s in debug log' % message)


def execute_command(cloud: Cloud, server: Server, command: str) -> Response:
    #FIXME: Remove this in all tests and use node.run
    if (command.startswith('scalarizr') or command.startswith('szradm')) and CONF.feature.dist.id == 'coreos':
        command = '/opt/bin/' + command
    node = cloud.get_node(server)
    LOG.info('Execute command on server: %s' % command)
    return node.run(command)


def get_scalaraizr_latest_version(branch: str) -> str:
    os_family = CONF.feature.dist.family
    index_url = get_repo_url(os_family, branch)
    LOG.debug('Check package from index_url: %s' % index_url)
    repo_data = parser_for_os_family(CONF.feature.dist.mask)(index_url=index_url)
    versions = [package['version'] for package in repo_data if
                package['name'] == 'scalarizr'] if os_family != 'coreos' else repo_data
    versions.sort(reverse=True)
    return versions[0]


def assert_scalarizr_version(server: Server, branch: str = None):
    #FIXME: Find other methods like this and leave only one
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


def assert_service_work(cloud: Cloud, server: Server, service: str, closed: bool = False):
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


def run_sysprep(cloud: Cloud, node: ExtendedNode):
    cmd = dict(
        gce='gcesysprep',
        ec2=PS_RUN_AS.format(
            command='''$doc = [xml](Get-Content 'C:/Program Files/Amazon/Ec2ConfigService/Settings/config.xml'); ''' \
                    '''$doc.Ec2ConfigurationSettings.Plugins.Plugin[0].State = 'Enabled'; ''' \
                    '''$doc.save('C:/Program Files/Amazon/Ec2ConfigService/Settings/config.xml')"; ''' \
                    '''cmd /C "'C:\Program Files\Amazon\Ec2ConfigService\ec2config.exe' -sysprep'''))
    try:
        node.run(cmd.get(node.platform_config.name))
    except Exception as e:
        LOG.error('Run sysprep exception : %s' % e.message)
    # Check that instance has stopped after sysprep
    end_time = time.time() + 900
    while time.time() <= end_time:
        cloud_node = [n for n in cloud.list_nodes() if n.uuid == node.uuid][0]
        LOG.debug('Obtained node after sysprep running: %s' % cloud_node)
        LOG.debug('Obtained node status after sysprep running: %s' % cloud_node.state)
        if cloud_node.state == NodeState.STOPPED:
            break
        time.sleep(10)
    else:
        raise AssertionError('Cloud instance is not in STOPPED status - sysprep failed, it state: %s' % node.state)


def install_scalarizr_to_server(server: Server, cloud: Cloud,
                                use_sysprep: bool = False,
                                use_rv_to_branch: bool = False,
                                custom_branch: str = None) -> str:
    """
    Install scalarizr to linux or windows server from branch
    :param server: Server for scalarizr
    :param cloud: Cloud object
    :param use_sysprep: If True and windows, run sysprep
    :param use_rv_to_branch: Get branch from RV_TO_BRANCH
    :param custom_branch: Use custom branch
    :return: Installed scalarizr version
    """
    if server:
        server.reload()
    LOG.debug('Cloud server not found get node from server')
    node = wait_until(cloud.get_node, args=(server,), timeout=300, logger=LOG)
    LOG.debug('Node get successfully: %s' % node)
    rv_branch = CONF.feature.branch
    rv_to_branch = CONF.feature.to_branch
    if use_rv_to_branch:
        branch = rv_to_branch
    elif custom_branch:
        branch = custom_branch
    else:
        branch = rv_branch
    LOG.info('Installing scalarizr from branch %s' % branch)
    scalarizr_ver = node.install_scalarizr(branch=branch)
    if use_sysprep and node.os.is_windows:
        run_sysprep(cloud, node)
    LOG.debug('Scalarizr %s was successfully installed' % scalarizr_ver)
    return scalarizr_ver


def assert_process_has_options(cloud: Cloud, server: Server, process: str, options: str):
    #TODO: Add systemd support
    LOG.debug('Checking options %s for process %s.' % (options, process))
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        for _ in range(3):
            out = conn.run('ps aux | grep %s' % process)
            LOG.debug('Grep for ps aux: %s' % out.std_out)
            for line in out.std_out.splitlines():
                if 'grep' in line:
                    continue
                LOG.info('Working with line: %s' % line)
                if options not in line and CONF.feature.dist != Dist('amzn1609') and not CONF.feature.dist.is_systemd:
                    raise AssertionError('Options %s are not in process, %s' % (
                        options, ' '.join(line.split()[10:])))
                else:
                    return True
        raise AssertionError('Process %s not found.' % process)


def deploy_agent(server: Server, cloud: Cloud):
    """Get install and deploy scripts from 'Deploy agent' page. Install and deploy agent"""
    #TODO: Add support for custom branch from drone
    scripts = IMPL.discovery_manager.triggering_agent_deployment(server.id)
    node = cloud.get_node(server)
    LOG.info(f'Install scalarizr to server {server.id}')
    node.run(scripts['install_cmd'])
    assert 'not found' not in node.run('scalarizr -v').std_out
    LOG.info(f'Run scalarizr: [{scripts["deploy_cmd"]}] on the imported server: {server.id}')
    assert not bool(node.run(scripts['deploy_cmd']).status_code)


def handle_agent_status(server: Server):
    timeout = 300
    time_until = time.time() + timeout
    while time.time() <= time_until:
        LOG.info('Check agent deploy status')
        agent_status = IMPL.discovery_manager.get_deployment_action_status(act='check', server_id=server.id)
        LOG.info(f'Agent deploy status: {agent_status}')
        if agent_status.get('status') == 'ready':
            break
        time.sleep(5)
    else:
        raise TimeoutError(f'Timeout: {timeout} seconds reached')


def create_image_from_node(node: ExtendedNode, cloud: Cloud) -> NodeImage:
    # Create an image
    platform = CONF.feature.platform
    image_name = 'tmp-base-{}-{:%d%m%Y-%H%M%S}'.format(
        CONF.feature.dist.id,
        datetime.now()
    )
    # Set credentials to image creation
    kwargs = {
        'node': node,
        'name': image_name
    }
    no_mapping = True if CONF.feature.dist.id == 'coreos' else False
    if platform.is_ec2:
        kwargs.update({'reboot': True})
    node.run('sync')
    image = cloud.create_template(no_mapping=no_mapping, **kwargs)
    assert getattr(image, 'id', False), f'An image from a node object {node.name} was not created'
    # Remove cloud server
    LOG.info(f'An image: {image.id} from a node object: {node.name} was created')
    # if platform.is_cloudstack:
    #     forwarded_port = world.forwarded_port
    #     ip = world.ip
    #     assert world.cloud.close_port(cloud_server, forwarded_port, ip=ip), "Can't delete a port forwarding rule."
    # LOG.info('Port forwarding rule was successfully removed.')
    if not platform.is_gce:
        assert node.destroy(), f"Can't destroy node: {node.id}."
    LOG.info(f'Cloud server {node.id} was successfully destroyed.')
    return image
