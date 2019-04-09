__author__ = 'gigimon'

import os
import time
import logging
import urllib2
import collections

from lettuce import world, step

from libcloud.compute.types import NodeState
from datetime import datetime

from revizor2.backend import IMPL
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.helpers.jsonrpc import ServiceError
from revizor2.helpers.parsers import parser_for_os_family, get_repo_url
from revizor2.defaults import DEFAULT_SERVICES_CONFIG, DEFAULT_API_TEMPLATES as templates, DEFAULT_PY3_BRANCH
from revizor2.consts import Dist, SERVICES_PORTS_MAP, BEHAVIORS_ALIASES, Platform
from revizor2 import szrapi
from revizor2.fixtures import tables

try:
    import winrm
except ImportError:
    raise ImportError("Please install WinRM")


PLATFORM_TERMINATED_STATE = collections.namedtuple('terminated_state', ('gce', 'ec2'))(
    'terminated',
    'stopped')

LOG = logging.getLogger(__name__)

#User data fixtures
#ec2 - (ec2, eucalyptus),  gce-gce, openstack-(openstack, ecs, rackspaceng), cloudstack-(cloudstack, idcf, ucloud)
USER_DATA = {
                Platform.EC2: {
                    "behaviors": "base,chef",
                    "farmid": "16674",
                    "message_format": "json",
                    "owner_email": "stunko@scalr.com",
                    "szr_key": "9gRW4akJmHYvh6W3vd6GzxOPtk/iQHL+8aZRZZ1u",
                    "s3bucket": "",
                    "cloud_server_id": "",
                    "env_id": "3414",
                    "server_index": "1",
                    "platform": "ec2",
                    "role": "base,chef",
                    "hash": "e6f1bfd5bbf612",
                    "custom.scm_branch": "master",
                    "roleid": "36318",
                    "farm_roleid": "60818",
                    "serverid": "96e52104-f5c4-4ce7-a018-c8c2eb571c99",
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "us-east-1",
                    "httpproto": "https",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "cloud_storage_path": "s3://"
                },

                Platform.GCE: {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "app",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60832",
                    "message_format": "json",
                    "realrolename": "apache-ubuntu1204-devel",
                    "region": "x-scalr-custom",
                    "httpproto": "https",
                    "szr_key": "NiR2xOZKVbvdMPgdxuayLjEK2xC7mtLkVTc0vpka",
                    "platform": "gce",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "app",
                    "cloud_server_id": "",
                    "roleid": "36319",
                    "env_id": "3414",
                    "serverid": "c2bc7273-6618-4702-9ea1-f290dca3b098",
                    "cloud_storage_path": "gcs://",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                },

                Platform.OPENSTACK: {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "base,chef",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60821",
                    "message_format": "json",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "ItalyMilano1",
                    "httpproto": "https",
                    "szr_key": "iyLO/+iOGFFcuSIxbr0IJteRwDjaP1t6NQ8kXbX6",
                    "platform": "ecs",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "base,chef",
                    "roleid": "36318",
                    "env_id": "3414",
                    "serverid": "59ddbdbf-6d69-4c53-a6b7-76ab391a8465",
                    "cloud_storage_path": "swift://",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                },

                Platform.CLOUDSTACK: {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "base,chef",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60826",
                    "message_format": "json",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "jp-east-f2v",
                    "httpproto": "https",
                    "szr_key": "cg3uuixg4jTUDz/CexsKpoNn0VZ9u6EluwpV+Mgi",
                    "platform": "idcf",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "base,chef",
                    "cloud_server_id": "",
                    "roleid": "36318",
                    "env_id": "3414",
                    "serverid": "feab131b-711e-4f4a-a7dc-ba083c28e5fc",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                }
}


class VerifyProcessWork(object):
    # NOTE: migrated
    @staticmethod
    def verify(server, behavior=None, port=None):
        if not behavior:
            behavior = server.role.behaviors[0]
        LOG.info('Verify %s behavior process work in server %s (on port: %s)' % (behavior, server.id, port))
        if hasattr(VerifyProcessWork, '_verify_%s' % behavior):
            return getattr(VerifyProcessWork, '_verify_%s' % behavior)(server, port)
        return True

    @staticmethod
    def _verify_process_running(server, process_name):
        LOG.debug('Check process %s in running state on server %s' % (process_name, server.id))
        node = world.cloud.get_node(server)
        with node.remote_connection() as conn:
            for i in range(3):
                out = node.run("ps -C %s -o pid=" % process_name)
                if not out.std_out.strip():
                    LOG.warning("Process %s don't work in server %s (attempt %s)" % (process_name, server.id, i))
                else:
                    LOG.info("Process %s work in server %s" % (process_name, server.id))
                    return True
                time.sleep(5)
            return False

    # @staticmethod
    # def _verify_open_port(server, port):
    #     for i in range(5):
    #         opened = world.check_open_port(server, port)
    #         if opened:
    #             return True
    #         time.sleep(15)
    #     return False

    @staticmethod
    def _verify_app(server, port):
        LOG.info('Verify apache (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        results = [VerifyProcessWork._verify_process_running(server,
                                                             DEFAULT_SERVICES_CONFIG['app'][
                                                                 node.os.family]['service_name']),
                   node.check_open_port(port)]
        return all(results)

    @staticmethod
    def _verify_www(server, port):
        LOG.info('Verify nginx (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        results = [VerifyProcessWork._verify_process_running(server, 'nginx'),
                   node.check_open_port(port)]
        return all(results)

    @staticmethod
    def _verify_redis(server, port):
        LOG.info('Verify redis-server (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        results = [VerifyProcessWork._verify_process_running(server, 'redis-server'),
                   node.check_open_port(port)]
        LOG.debug('Redis-server verifying results: %s' % results)
        return all(results)

    @staticmethod
    def _verify_scalarizr(server, port=8010):
        LOG.info('Verify scalarizr (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        if CONF.feature.platform.is_cloudstack and world.cloud._driver.use_port_forwarding():
            port = server.details['scalarizr.ctrl_port']
        results = [VerifyProcessWork._verify_process_running(server, 'scalarizr'),
                   VerifyProcessWork._verify_process_running(server, 'scalr-upd-client'),
                   node.check_open_port(port)]
        LOG.debug('Scalarizr verifying results: %s' % results)
        return all(results)

    @staticmethod
    def _verify_memcached(server, port):
        LOG.info('Verify memcached (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        results = [VerifyProcessWork._verify_process_running(server, 'memcached'),
                   node.check_open_port(port)]
        return all(results)


@step('I execute \'(.+)\' in (.+)$')
def execute_command(step, command, serv_as):
    # NOTE: migrated
    if (command.startswith('scalarizr') or command.startswith('szradm')) and CONF.feature.dist.id == 'coreos':
        command = '/opt/bin/' + command
    node = world.cloud.get_node(getattr(world, serv_as))
    LOG.info('Execute command on server: %s' % command)
    node.run(command)


@step('I change repo in ([\w\d]+) to system$')
def change_repo(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    change_repo_to_branch(node, CONF.feature.branch)


def change_repo_to_branch(node, branch):
    if 'ubuntu' in node.os.id or 'debian' in node.os.id:
        LOG.info('Change repo in Ubuntu')
        node.put_file('/etc/apt/sources.list.d/scalr-branch.list',
                      'deb http://buildbot.scalr-labs.com/apt/debian %s/\n' % branch)
    elif 'centos' in node.os.id:
        LOG.info('Change repo in CentOS')
        node.put_file('/etc/yum.repos.d/scalr-stable.repo',
                      '[scalr-branch]\n' +
                      'name=scalr-branch\n' +
                      'baseurl=http://buildbot.scalr-labs.com/rpm/%s/rhel/$releasever/$basearch\n' % branch +
                      'enabled=1\n' +
                      'gpgcheck=0\n' +
                      'protect=1\n')


@step('pin([ \w]+)? repo in ([\w\d]+)$')
def pin_repo(step, repo, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if repo and repo.strip() == 'system':
        branch = CONF.feature.branch.replace('/', '-').replace('.', '').strip()
    else:
        branch = os.environ.get('RV_TO_BRANCH', 'master').replace('/', '-').replace('.', '').strip()
    if 'ubuntu' in node.os.id:
        LOG.info('Pin repository for branch %s in Ubuntu' % branch)
        node.put_file('/etc/apt/preferences',
                      'Package: *\n' +
                      'Pin: release a=%s\n' % branch +
                      'Pin-Priority: 990\n')
    elif 'centos' in node.os.id:
        LOG.info('Pin repository for branch %s in CentOS' % repo)
        node.run('yum install yum-protectbase -y')


@step('update scalarizr in ([\w\d]+)$')
def update_scalarizr(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    platform = CONF.feature.platform
    if 'ubuntu' in node.os.id:
        LOG.info('Update scalarizr in Ubuntu')
        node.run('apt-get update')
        node.run('apt-get install scalarizr-base scalarizr-%s -y' % platform.name)
    elif 'centos' in node.os.id:
        LOG.info('Update scalarizr in CentOS')
        node.run('yum install scalarizr-base scalarizr-%s -y' % platform.name)


@step('process ([\w-]+) is (not\s)*running in ([\w\d]+)$')
def check_process(step, process, negation, serv_as):
    LOG.info("Check running process %s on server" % process)
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    list_proc = node.run('ps aux | grep %s' % process).std_out.split('\n')
    processes = filter(lambda x: 'grep' not in x and x, list_proc)
    msg = "Process {} on server {} not in valid state".format(
        process,
        server.id)
    assert not processes if negation else processes, msg


@step(r'(\d+) port is( not)? listen on ([\w\d]+)')
def verify_port_status(step, port, closed, serv_as):
    server = getattr(world, serv_as)
    if port.isdigit():
        port = int(port)
    else:
        port = SERVICES_PORTS_MAP[port]
        if isinstance(port, collections.Iterable):
            port = port[0]
    closed = True if closed else False
    LOG.info('Verify port %s is %s on server %s' % (
        port, 'closed' if closed else 'open', server.id
    ))
    node = world.cloud.get_node(server)
    if not CONF.feature.dist.is_windows:
        world.set_iptables_rule(server, port)
    if CONF.feature.platform.is_cloudstack and world.cloud._driver.use_port_forwarding():
        port = world.cloud.open_port(node, port, ip=server.public_ip)

    results = []
    for attempt in range(3):
        results.append(node.check_open_port(port))
        time.sleep(5)

    if closed and results[-1]:
        raise AssertionError('Port %s is open on server %s (attempts: %s)' % (port, server.id, results))
    elif not closed and not results[-1]:
        raise AssertionError('Port %s is closed on server %s (attempts: %s)' % (port, server.id, results))


@step(r'([\w-]+(?!process)) is( not)? running on (.+)')
@world.run_only_if(dist=['!coreos'])
def assert_check_service(step, service, closed, serv_as): #FIXME: Rewrite this ugly logic
    # NOTE: migrated
    server = getattr(world, serv_as)
    port = SERVICES_PORTS_MAP[service]
    if isinstance(port, collections.Iterable):
        port = port[0]
    closed = True if closed else False
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
    node = world.cloud.get_node(server)
    if not CONF.feature.dist.is_windows:
        world.set_iptables_rule(server, port)
    if CONF.feature.platform.is_cloudstack and world.cloud._driver.use_port_forwarding():
        #TODO: Change login on this behavior
        port = world.cloud.open_port(node, port, ip=server.public_ip)
    if service in BEHAVIORS_ALIASES.values():
        behavior = [x[0] for x in BEHAVIORS_ALIASES.items() if service in x][0]
    else:
        behavior = service
    check_result = VerifyProcessWork.verify(server, behavior, port)
    if closed and check_result:
        raise AssertionError("Service %s must be don't work but it work!" % service)
    if not closed and not check_result:
        raise AssertionError("Service %s must be work but it doesn't work! (results: %s)" % (service, check_result))


@step(r'I (\w+) service ([\w\d]+) in ([\w\d]+)')
def service_control(step, action, service, serv_as):
    LOG.info("%s service %s" % (action.title(), service))
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('/etc/init.d/%s %s' % (service, action))


@step(r'scalarizr debug log in ([\w\d]+) contains \'(.+)\'')
def find_string_in_debug_log(step, serv_as, string):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    out = node.run('grep "%s" /var/log/scalarizr_debug.log' % string)
    if not string in out.std_out:
        raise AssertionError('String "%s" not found in scalarizr_debug.log. Grep result: %s' % (string, out))




@step('scalarizr version from (\w+) repo is last in (.+)$')
@world.passed_by_version_scalarizr('2.5.14')
def assert_scalarizr_version_old(step, repo, serv_as):
    """
    Argument repo can be system or role.
    System repo - CONF.feature.branch
    Role repo - CONF.feature.to_branch
    """
    if repo == 'system':
        branch = CONF.feature.branch
    elif repo == 'role':
        branch = CONF.feature.to_branch
    server = getattr(world, serv_as)
    if branch == 'latest' and 'base' in server.role.behaviors:
        branch = DEFAULT_PY3_BRANCH
    os_family = Dist(server.role.dist).family
    index_url = get_repo_url(os_family, branch)
    repo_data = parser_for_os_family(server.role.dist)(index_url=index_url)
    versions = [package['version'] for package in repo_data if package['name'] == 'scalarizr']
    versions.sort()
    LOG.info('Scalarizr versions in repository %s: %s' % (branch, versions))
    server_info = server.upd_api.status(cached=False)
    LOG.debug('Server %s status: %s' % (server.id, server_info))
    # if not repo == server_info['repository']:
    #     raise AssertionError('Scalarizr installed on server from different repo (%s) must %s'
    #                          % (server_info['repository'], repo))
    if not versions[-1] == server_info['installed']:
        raise AssertionError('Installed scalarizr version is not last! Installed %s, last: %s'
                             % (server_info['installed'], versions[-1]))


@step(r'scalarizr version(?:\sfrom\s([\w\d_]+))* is last in ([\w\d]+)$')
def assert_scalarizr_version(step, branch, serv_as):
    """
    Argument branch can be system or role.
    System branch - CONF.feature.branch
    Role branch - CONF.feature.to_branch
    """
    #FIXME: Rewrite this ugly code!
    # NOTE: migrated
    server = getattr(world, serv_as)
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
        versions = [package['version'] for package in repo_data if package['name'] == 'scalarizr'] if os_family != 'coreos' else repo_data
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
        except urllib2.URLError:
            time.sleep(3)
    else:
        raise AssertionError('Can\'t get access to update client 5 times (15 seconds)')
    LOG.debug('Last scalarizr version from update client status: %s' % update_status['installed'])
    if not update_status['state'] == 'noop' and update_status['prev_state'] == 'completed':
        assert update_status['state'] == 'completed', \
            'Update client not in normal state. Status = "%s", Previous state = "%s"' % \
            (update_status['state'], update_status['prev_state'])
    assert last_version == installed_version, \
        'Server not has last build of scalarizr package, installed: %s last_version: %s' % (installed_version, last_version)


@step('I reboot scalarizr in (.+)$')
def reboot_scalarizr(step, serv_as):
    # NOTE: migrated
    server = getattr(world, serv_as)
    if CONF.feature.dist.is_systemd:
        cmd = "systemctl restart scalarizr"
    else:
        cmd = "/etc/init.d/scalarizr restart"
    node = world.cloud.get_node(server)
    node.run(cmd)
    LOG.info('Scalarizr restart complete')
    time.sleep(15)


@step('see "(.+)" in ([\w]+) log')
def check_log(step, message, serv_as):
    # NOTE: migrated
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Check scalarizr log for  termination')
    wait_until(world.check_text_in_scalarizr_log, timeout=300, args=(node, message),
               error_text='Not see %s in debug log' % message)


@step('I ([\w\d]+) service ([\w\d]+)(?: and ([\w]+) has been changed)? on ([\w\d]+)(?: by ([\w]+))?')
def change_service_status(step, status_as, behavior, is_change_pid, serv_as, is_api):
    """Change process status on remote host by his name. """
    #Init params
    service = {'node': None}
    server = getattr(world, serv_as)
    is_api = True if is_api else False
    is_change_pid = True if is_change_pid else False
    node = world.cloud.get_node(server)

    #Checking the behavior in the role
    if not behavior in server.role.behaviors and behavior != 'scalarizr':
        raise AssertionError("{0} can not be found in the tested role.".format(behavior))

    #Get behavior configs
    common_config = DEFAULT_SERVICES_CONFIG.get(behavior)
    #Get service name & status
    if common_config:
        status = common_config['api_endpoint']['service_methods'].get(status_as) if is_api else status_as
        service.update({'node': common_config.get('service_name')})
        if not service['node']:
            service.update({'node': common_config.get(node.os.family).get('service_name')})
        if is_api:
            service.update({'api': common_config['api_endpoint'].get('name')})
            if not service['api']:
                raise AssertionError("Can't {0} service. "
                                     "The api endpoint name is not found by the bahavior name {1}".format(status_as, behavior))
            if not status:
                raise AssertionError("Can't {0} service. "
                                     "The api call is not found for {1}".format(status_as, service['node']))
    if not service['node']:
        raise AssertionError("Can't {0} service. "
                             "The process name is not found by the bahavior name {1}".format(status_as, behavior))
    LOG.info("Change service status: {0} {1} {2}".format(service['node'], status, 'by api call' if is_api else ''))

    #Change service status, get pids before and after
    res = world.change_service_status(server, service, status, use_api=is_api, change_pid=is_change_pid)

    #Verify change status
    if any(pid in res['pid_before'] for pid in res['pid_after']):
        LOG.error('Service change status info: {0} Service change status error: {1}'.format(res['info'].std_out, res['info'].std_err)
        if not is_api
        else 'Status of the process has not changed, pid have not changed. pib before: %s pid after: %s' % (res['pid_before'], res['pid_after']))
        raise AssertionError("Can't {0} service. No such process {1}".format(status_as, service['node']))

    LOG.info('Service change status info: {0}'.format(res['info'].std_out if not is_api
        else '%s.%s() complete successfully' % (service['api'], status)))
    LOG.info("Service status was successfully changed : {0} {1} {2}".format(service['node'], status_as,
                                                                            'by api call' if is_api else ''))
    time.sleep(15)


@step('I know ([\w]+) storages$')
def get_ebs_for_instance(step, serv_as):
    """Give EBS storages for server"""
    #TODO: Add support for all platform with persistent disks
    server = getattr(world, serv_as)
    volumes = server.get_volumes()
    platform = CONF.feature.platform
    LOG.debug('Volumes for server %s is: %s' % (server.id, volumes))
    if platform.is_ec2:
        storages = filter(lambda x: 'sda' not in x.extra['device'], volumes)
    elif platform.is_cloudstack:
        storages = filter(lambda x: x.extra['volume_type'] == 'DATADISK', volumes)
    else:
        return
    LOG.info('Storages for server %s is: %s' % (server.id, storages))
    if not storages:
        raise AssertionError('Server %s not have storages (%s)' % (server.id, storages))
    setattr(world, '%s_storages' % serv_as, storages)


@step('([\w]+) storage is (.+)$')
def check_ebs_status(step, serv_as, status):
    """Check EBS storage status"""
    if CONF.feature.platform.is_gce:
        return
    time.sleep(30)
    server = getattr(world, serv_as)
    wait_until(world.check_server_storage, args=(serv_as, status), timeout=300, error_text='Volume from server %s is not %s' % (server.id, status))


@step('change branch in server ([\w\d]+) in sources to ([\w\d]+)')
def change_branch_in_sources(step, serv_as, branch):
    if 'system' in branch:
        branch = CONF.feature.branch
    elif not branch.strip():
        branch = CONF.feature.to_branch
    else:
        branch = branch.replace('/', '-').replace('.', '').strip()
    server = getattr(world, serv_as)
    LOG.info('Change branches in sources list in server %s to %s' % (server.id, branch))
    node = world.cloud.get_node(server)
    with node.remote_connection() as conn:
        if node.os.is_debian:
            LOG.debug('Change in debian')
            for repo_file in ['/etc/apt/sources.list.d/scalr-stable.list', '/etc/apt/sources.list.d/scalr-latest.list']:
                LOG.info("Change branch in %s to %s" % (repo_file, branch))
                conn.run('echo "deb http://buildbot.scalr-labs.com/apt/debian %s/" > %s' % (branch, repo_file))
        elif node.os.is_centos:
            LOG.debug('Change in centos')
            for repo_file in ['/etc/yum.repos.d/scalr-stable.repo']:
                LOG.info("Change branch in %s to %s" % (repo_file, branch))
                conn.run('echo "[scalr-branch]\nname=scalr-branch\nbaseurl=http://buildbot.scalr-labs.com/rpm/%s/rhel/\$releasever/\$basearch\nenabled=1\ngpgcheck=0" > %s' % (branch, repo_file))
            conn.run('echo > /etc/yum.repos.d/scalr-latest.repo')
        elif node.os.is_windows:
            for repo_file in ['C:\Program Files\Scalarizr\etc\scalr-latest.winrepo',
                              'C:\Program Files\Scalarizr\etc\scalr-stable.winrepo']:
                # LOG.info("Change branch in %s to %s" % (repo_file, branch))
                conn.run('echo http://buildbot.scalr-labs.com/win/%s/x86_64/ > "%s"' % (branch, repo_file))


# Step used revizor2.szrapi classes functional
@step(r'I run (.+) command (.+) and pid has been changed on (\w+)(?:(.+))?')
def change_service_pid_by_api(step, service_api, command, serv_as, isset_args=None):
    """
        :param service_api: Service Api class name
        :param command: Api command
        :param serv_as: Server name
        :param isset_args: Is api command has extended arguments
    """
    #Get process pid
    def get_pid(pattern):
        if not pattern:
            raise Exception("Can't get service pid, service search condition is empty.")
        if isinstance(pattern, (list, tuple)):
            pattern = [str(element).strip() for element in pattern]
        else:
            pattern = [element.strip() for element in str(pattern).split(',')]
        cmd = "ps aux | grep {pattern} | grep -v grep | awk {{print'$2'}}".format(pattern='\|'.join(pattern))
        return node.run(cmd).std_out.rstrip('\n').split('\n')

    # Set attributes
    server = getattr(world, serv_as)
    service_api = service_api.strip().replace('"', '')
    command = command.strip().replace('"', '')
    node = world.cloud.get_node(server)

    # Get service api
    api = getattr(getattr(szrapi, service_api)(server), command)
    LOG.debug('Set %s instance %s for server %s' % (service_api, api, server.id))
    # Get api arguments
    args = {}
    if isset_args:
        LOG.debug('Api method: (%s) extended arguments: %s' % (command, step.hashes))
        for key, value in step.hashes[0].iteritems():
            try:
                if value.isupper():
                    args.update({key: templates[service_api][value.lower()]})
                else:
                    args.update({key: eval(value)})
            except Exception:
                args.update({key: value})
        LOG.debug('Save {0}.{1} extended arguments: {2}'.format(
            service_api,
            command,
            args
        ))

    # Get service search pattern
    pattern = args.get('ports', None)
    if not pattern:
        # Get behavior from role
        behavior = server.role.behaviors[0]
        common_config = DEFAULT_SERVICES_CONFIG.get(behavior)
        pattern = common_config.get('service_name',
                                    common_config.get(node.os.family).get('service_name'))
    LOG.debug('Set search condition: (%s) to get service pid.' % pattern)
    # Run api command
    pid_before = get_pid(pattern)
    LOG.debug('Obtained service:%s pid list %s before api call.' % (pattern, pid_before))
    api_result = api(**args) if args else api()
    LOG.debug('Run %s instance method %s.' % (service_api, command))
    # Save api command result to world [command_name]_res
    setattr(world, ''.join((command, '_res')), api_result)
    LOG.debug('Save {0} instance method {1} result: {2}'.format(
        service_api,
        command,
        api_result))
    pid_after = get_pid(pattern)
    LOG.debug('Obtained service:%s pid list %s after api call.' % (pattern, pid_after))
    assertion_message = 'Some pid was not be changed. pid before api call: {0} after: {1}'.format(
        pid_before,
        pid_after)
    assert not any(pid in pid_before for pid in pid_after), assertion_message


@step(r'I create ([\w]+-?[\w]+?\s)?image from deployed server')
def creating_image(step, image_type=None):
    # NOTE: migrated
    image_type = image_type or 'base'
    cloud_server = getattr(world, 'cloud_server')
    # Create an image
    platform = CONF.feature.platform
    image_name = 'tmp-{}-{}-{:%d%m%Y-%H%M%S}'.format(
        image_type.strip(),
        CONF.feature.dist.id,
        datetime.now()
    )
    # Set credentials to image creation
    kwargs = dict(
        node=cloud_server,
        name=image_name,
    )
    no_mapping = True if CONF.feature.dist.id == 'coreos' else False
    if platform.is_ec2:
        kwargs.update({'reboot': True})
    cloud_server.run('sync')
    image = world.cloud.create_template(no_mapping=no_mapping, **kwargs)
    assert getattr(image, 'id', False), 'An image from a node object %s was not created' % cloud_server.name
    # Remove cloud server
    LOG.info('An image: %s from a node object: %s was created' % (image.id, cloud_server.name))
    setattr(world, 'image', image)
    LOG.debug('Image attrs: %s' % dir(image))
    LOG.debug('Image Name: %s' % image.name)
    if platform.is_cloudstack:
        forwarded_port = world.forwarded_port
        ip = world.ip
        assert world.cloud.close_port(cloud_server, forwarded_port, ip=ip), "Can't delete a port forwarding rule."
    LOG.info('Port forwarding rule was successfully removed.')
    if not platform.is_gce:
        assert cloud_server.destroy(), "Can't destroy node: %s." % cloud_server.id
    LOG.info('Virtual machine %s was successfully destroyed.' % cloud_server.id)
    setattr(world, 'cloud_server', None)


@step(r'I add ([\w]+-?[\w]+?\s)?image to the new roles?(\sas non scalarized)*$')
def creating_role(step, image_type=None, non_scalarized=None):
    # NOTE: migrated but with changes!
    image = getattr(world, 'image')
    image_type = (image_type or 'base').strip()
    platform = CONF.feature.platform

    if platform.is_gce:
        cloud_location = ""
        image_id = image.extra['selfLink'].split('projects')[-1][1:]
    elif platform.is_azure:
        cloud_location = platform.location
        image_id = '/'.join(image.name.split(' ')[:-1]) + '/latest'
    else:
        cloud_location = platform.location
        image_id = image.id

    image_kwargs = dict(
        platform=platform.name,
        cloud_location=cloud_location,
        image_id=image_id
    )
    if platform.is_azure:
        image_kwargs['cloud_location'] = ""
    name = 'tmp-{}-{}-{:%d%m%Y-%H%M%S}'.format(
            image_type,
            CONF.feature.dist.id,
            datetime.now())
    if 'base' not in image_type:
        behaviors = getattr(world, 'installed_behaviors', None)
    else:
        behaviors = ['chef'] if CONF.feature.dist.id != 'coreos' else ['base']
    # Checking an image
    try:
        LOG.debug('Checking an image {image_id}:{platform}({cloud_location})'.format(**image_kwargs))
        image_check_result = IMPL.image.check(**image_kwargs)
        image_registered = False
    except Exception as e:
        if not ('Image has already been registered' in e.message):
            raise
        image_registered = True
    is_scalarized = False if non_scalarized else True
    has_cloudinit = True if ('cloudinit' in image_type and not is_scalarized) else False
    if not image_registered:
        # Register image to the Scalr
        LOG.debug('Register image %s to the Scalr' % name)
        image_kwargs.update(dict(
            software=behaviors,
            name=name,
            is_scalarized=is_scalarized,
            has_cloudinit=has_cloudinit,
            image_volumes=image_check_result.get('volumes', None)))
        image = IMPL.image.create(**image_kwargs)
    else:
        image = IMPL.image.get(image_id=image_id)
    # Create new role
    for behavior in behaviors:
        if has_cloudinit:
            role_name = name.replace(image_type, '-'.join((behavior, 'cloudinit')))
            role_behaviors = list((behavior, 'chef'))
        else:
            role_name = name
            role_behaviors = behaviors
        if len(role_name) > 50:
            role_name = role_name[:50].strip('-')
        role_kwargs = dict(
            name=role_name,
            is_scalarized=int(is_scalarized or has_cloudinit),
            behaviors=role_behaviors,
            images=[dict(
                platform=platform.name,
                cloudLocation=cloud_location,
                hash=image['hash'])])
        LOG.debug('Create new role {name}. Role options: {behaviors} {images}'.format(**role_kwargs))
        role = IMPL.role.create(**role_kwargs)
        if not has_cloudinit:
            setattr(world, 'role', role['role'])


def run_sysprep(node):
    # NOTE: migrated
    cmd = dict(
        gce='gcesysprep',
        ec2=world.PS_RUN_AS.format(
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
        cloud_node = (filter(lambda n: n.uuid == node.uuid, world.cloud.list_nodes()) or [''])[0]
        LOG.debug('Obtained node after sysprep running: %s' % cloud_node)
        LOG.debug('Obtained node status after sysprep running: %s' % cloud_node.state)
        if cloud_node.state == NodeState.STOPPED:
            break
        time.sleep(10)
    else:
        raise AssertionError('Cloud instance is not in STOPPED status - sysprep failed, it state: %s' % node.state)


def get_user_name():
    platform = CONF.feature.platform
    if (platform.is_gce or platform.is_azure):
        user_name = ['scalr']
    elif CONF.feature.dist.dist == 'ubuntu':
        user_name = ['root', 'ubuntu']
    elif CONF.feature.dist.dist == 'amazon' or \
            (CONF.feature.dist.dist == 'redhat' and platform.is_ec2):
        user_name = ['root', 'ec2-user']
    else:
        user_name = ['root']
    return user_name


def get_repo_type(custom_branch, custom_version=None):
    class RepoTypes(dict):

        def __init__(self, branch, version=None):
            dict.__init__(self)
            ci_repo = CONF.feature.ci_repo.lower()
            version = version or ''
            self.update({
                'release': '{branch}'.format(branch=branch),
                'develop': '{ci}/{branch}'.format(ci=ci_repo, branch=branch),
                'snapshot': 'snapshot/{version}'.format(version=version)})

        def __extend_repo_type(self, value):
            rt = value.split('/')
            rt.insert(1, CONF.feature.platform.name)
            return '/'.join(rt)

        def __getitem__(self, key):
            if self.has_key(key):
                value = dict.__getitem__(self, key)
                if not CONF.feature.dist.is_windows:
                    value = self.__extend_repo_type(value)
                return value
            raise AssertionError('Repo type: "%s" not valid' % key)

        def get(self, key):
            return self.__getitem__(key)

    # Getting repo types for os family
    repo_types = RepoTypes(branch=custom_branch, version=custom_version)
    # Getting repo
    if custom_version:
        repo_type = repo_types.get('snapshot')
    elif custom_branch in ['latest', 'stable']:
        repo_type = repo_types.get('release')
    else:
        repo_type = repo_types.get('develop')
    return repo_type


@step(r"I install(?: new)? scalarizr(?: ([\w\d\.\'\-]+))?(?: (with sysprep))? to the server(?: ([\w][\d]))?(?: (manually))?(?: from the branch ([\w\d\W]+))?")
def installing_scalarizr(step, custom_version=None, use_sysprep=None, serv_as=None, use_rv_to_branch=None, custom_branch=None):
    # NOTE: migrated
    node = getattr(world, 'cloud_server', None)
    resave_node = True if node else False
    server = getattr(world, (serv_as or '').strip(), None)
    if server:
        server.reload()
    if not node:
        LOG.debug('Cloud server not found get node from server')
        node = wait_until(world.cloud.get_node, args=(server, ), timeout=300, logger=LOG)
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
        run_sysprep(node)
    setattr(world, 'pre_installed_agent', scalarizr_ver)
    if resave_node:
        setattr(world, 'cloud_server', node)
    LOG.debug('Scalarizr %s was successfully installed' % scalarizr_ver)


@step('I have a server([\w ]+)? running in cloud$')
def given_server_in_cloud(step, user_data):
    # Moved to lifecycle/common/discovery
    #TODO: Add install behaviors
    LOG.info('Create node in cloud. User_data:%s' % user_data)
    #Convert dict to formatted str
    platform = CONF.feature.platform
    if user_data:
        dict_to_str = lambda d: ';'.join(['='.join([key, value]) if value else key for key, value in d.iteritems()])
        user_data = dict_to_str(USER_DATA[platform.cloud_family])
        if platform.is_gce:
            user_data = {'scalr': user_data}
    else:
        user_data = None
    #Create node
    image = None
    if CONF.feature.dist.is_windows or CONF.feature.dist.id == 'coreos':
        table = tables('images-clean')
        search_cond = dict(
            dist=CONF.feature.dist.id,
            platform=platform.name)
        image = table.filter(search_cond).first().keys()[0].encode('ascii', 'ignore')
    node = world.cloud.create_node(userdata=user_data, image=image)
    setattr(world, 'cloud_server', node)
    LOG.info('Cloud server was set successfully node name: %s' % node.name)
    if platform.is_cloudstack:
        #Run command
        out = node.run('wget -qO- ifconfig.me/ip')
        if not out.std_err:
            ip_address = out[0].rstrip("\n")
            LOG.info('Received external ip address of the node. IP:%s' % ip_address)
            setattr(world, 'ip', ip_address)
        else:
            raise AssertionError("Can't get node external ip address. Original error: %s" % out.std_err)
        #Open port, set firewall rule
        new_port = world.cloud.open_port(node, 8013, ip=ip_address)
        setattr(world, 'forwarded_port', new_port)
        if not new_port == 8013:
            raise AssertionError('Import will failed, because opened port is not 8013, '
                                 'an installed port is: %s' % new_port)


@step("ports \[([\d,]+)\] (not )?in iptables in ([\w\d]+)")
@world.run_only_if(platform=['!%s' % Platform.RACKSPACENGUS, '!%s' % Platform.CLOUDSTACK],
    dist=['!scientific6', '!centos-6-x', '!centos-7-x', '!coreos'])
def verify_ports_in_iptables(step, ports, should_not_contain, serv_as):
    LOG.info('Verify ports "%s" in iptables' % ports)
    if CONF.feature.platform.is_cloudstack:
        LOG.info('Not check iptables because CloudStack')
        return
    server = getattr(world, serv_as)
    ports = ports.split(',')
    node = world.cloud.get_node(server)
    iptables_rules = node.run('iptables -L').std_out
    LOG.debug('iptables rules:\n%s' % iptables_rules)
    for port in ports:
        LOG.debug('Check port "%s" in iptables rules' % port)
        if port in iptables_rules and should_not_contain:
            raise AssertionError('Port "%s" in iptables rules!' % port)
        elif not should_not_contain and port not in iptables_rules:
            raise AssertionError('Port "%s" is NOT in iptables rules!' % port)


@step("ports \[([\d,]+)\] (not )?in semanage in ([\w\d]+)")
@world.run_only_if(family='centos')
def verify_ports_in_semanage(step, ports, should_not_contain, serv_as):
    server = getattr(world, serv_as)
    ports = ports.split(',')
    node = world.cloud.get_node(server)
    semanage_rules = node.run('semanage port -l | grep http_port').std_out
    LOG.debug('semanage rules:\n%s' % semanage_rules)
    for port in ports:
        LOG.debug('Check port "%s" in semanage rules' % port)
        if port in semanage_rules and should_not_contain:
            raise AssertionError('Port "%s" in semanage rules!' % port)
        elif not should_not_contain and not port in semanage_rules:
            raise AssertionError('Port "%s" is NOT in semanage rules!' % port)
