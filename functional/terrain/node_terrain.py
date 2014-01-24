__author__ = 'gigimon'
import os
import time
import logging
import collections

from lettuce import world, step

from revizor2 import consts
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.defaults import DEFAULT_SERVICES_CONFIG
from revizor2.consts import Platform, Dist, SERVICES_PORTS_MAP, BEHAVIORS_ALIASES


LOG = logging.getLogger(__name__)


class VerifyProcessWork(object):

    @staticmethod
    def verify(server, behavior=None, port=None):
        if not behavior:
            behavior = server.role.behaviors[0]
        LOG.info('Verify %s behavior process work in server %s (on port: %s)' % (behavior, server.id, port))
        if hasattr(VerifyProcessWork, '_verify_%s' % behavior):
            return getattr(VerifyProcessWork, '_verify_%s' % behavior)(server, port)

    @staticmethod
    def _verify_process_running(server, process_name):
        LOG.debug('Check process %s in running state on server %s' % (process_name, server.id))
        node = world.cloud.get_node(server)
        out = node.run("pgrep -l %s | awk {print'$1'}" % process_name)
        if not out[0].strip():
            LOG.warning("Process %s don't work in server %s" % (process_name, server.id))
            return False
        LOG.info("Process %s work in server %s" % (process_name, server.id))
        return True

    @staticmethod
    def _verify_open_port(server, port):
        return world.check_open_port(server, port)

    @staticmethod
    def _verify_app(server, port):
        LOG.info('Verify apache (%s) work in server %s' % (port, server.id))
        node = world.cloud.get_node(server)
        results = [VerifyProcessWork._verify_process_running(server,
                                                             DEFAULT_SERVICES_CONFIG['app'][
                                                                 Dist.get_os_family(node.os[0])]['service_name']),
                   VerifyProcessWork._verify_open_port(server, port)]
        return all(results)

    @staticmethod
    def _verify_www(server, port):
        LOG.info('Verify nginx (%s) work in server %s' % (port, server.id))
        results = [VerifyProcessWork._verify_process_running(server, 'nginx'),
                   VerifyProcessWork._verify_open_port(server, port)]
        return all(results)

    @staticmethod
    def _verify_scalarizr(server, port):
        LOG.info('Verify scalarizr (%s) work in server %s' % (port, server.id))
        results = [VerifyProcessWork._verify_process_running(server, 'scalarizr'),
                   VerifyProcessWork._verify_process_running(server, 'scalr-upd-client'),
                   VerifyProcessWork._verify_open_port(server, port)]
        return all(results)


@step('I change repo in ([\w\d]+)$')
def change_repo(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    branch = os.environ.get('RV_TO_BRANCH', 'master').replace('/', '-').replace('.', '').strip()
    change_repo_to_branch(node, branch)


@step('I change repo in ([\w\d]+) to system$')
def change_repo(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    change_repo_to_branch(node, CONF.feature.branch.replace('/', '-').replace('.', '').strip())


def change_repo_to_branch(node, branch):
    if 'ubuntu' in node.os[0].lower() or 'debian' in node.os[0].lower():
        LOG.info('Change repo in Ubuntu')
        node.put_file('/etc/apt/sources.list.d/scalr-branch.list',
                      'deb http://buildbot.scalr-labs.com/apt/debian %s/\n' % branch)
    elif 'centos' in node.os[0].lower():
        LOG.info('Change repo in CentOS')
        node.put_file('/etc/yum.repos.d/scalr-stable.repo',
                      '[scalr-branch]\n' +
                      'name=scalr-branch\n' +
                      'baseurl=http://buildbot.scalr-labs.com/rpm/%s/rhel/$releasever/$basearch\n' % branch +
                      'enabled=1\n' +
                      'gpgcheck=0\n' +
                      'protect=1\n')


@step('pin (\w+) repo in ([\w\d]+)$')
def pin_repo(step, repo, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if repo == 'system':
        branch = CONF.feature.branch
    else:
        branch = os.environ.get('RV_TO_BRANCH', 'master')
    if 'ubuntu' in node.os[0].lower():
        LOG.info('Pin repository for branch %s in Ubuntu' % branch)
        node.put_file('/etc/apt/preferences',
                      'Package: *\n' +
                      'Pin: release a=%s\n' % branch +
                      'Pin-Priority: 990\n')
    elif 'centos' in node.os[0].lower():
        LOG.info('Pin repository for branch %s in CentOS' % repo)
        node.run('yum install yum-protectbase -y')


@step('update scalarizr in ([\w\d]+)$')
def update_scalarizr(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if 'ubuntu' in node.os[0].lower():
        LOG.info('Update scalarizr in Ubuntu')
        node.run('apt-get update')
        node.run('apt-get install scalarizr-base scalarizr-%s -y' % CONF.feature.driver.cloud_family)
    elif 'centos' in node.os[0].lower():
        LOG.info('Update scalarizr in CentOS')
        node.run('yum install scalarizr-base scalarizr-%s -y' % CONF.feature.driver.cloud_family)



@step('process ([\w-]+) is running in ([\w\d]+)$')
def check_process(step, process, serv_as):
    LOG.info("Check running process %s on server" % process)
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    list_proc = node.run('ps aux | grep %s' % process)[0]
    for p in list_proc.splitlines():
        if not 'grep' in p and process in p:
            return True
    raise AssertionError("Process %s is not running in server %s" % (process, server.id))


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
    if not CONF.feature.dist.startswith('win'):
        world.set_iptables_rule(server, port)
    if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        port = world.cloud.open_port(node, port, ip=server.public_ip)

    results = []
    for attempt in range(3):
        results.append(world.check_open_port(server, port))
        time.sleep(5)

    if closed and any(results):
        raise AssertionError('Port %s is open on server %s (attempts: %s)' % (port, server.id, results))
    elif not closed and not all(results):
        raise AssertionError('Port %s is closed on server %s (attempts: %s)' % (port, server.id, results))


@step(r'([\w-]+) is( not)? running on (.+)')
def assert_check_service(step, service, closed, serv_as):
    server = getattr(world, serv_as)
    port = SERVICES_PORTS_MAP[service]
    if isinstance(port, collections.Iterable):
        port = port[0]
    closed = True if closed else False
    LOG.info('Verify port %s is %s on server %s' % (
        port, 'closed' if closed else 'open', server.id
    ))
    node = world.cloud.get_node(server)
    if not CONF.feature.dist.startswith('win'):
        world.set_iptables_rule(server, port)
    if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        port = world.cloud.open_port(node, port, ip=server.public_ip)
    if service in BEHAVIORS_ALIASES.values():
        behavior = [x[0] for x in BEHAVIORS_ALIASES.items() if service in x][0]
    else:
        behavior = service
    check_result = VerifyProcessWork.verify(server, behavior, port)
    if closed and check_result:
        raise AssertionError("Service %s must be don't work but it work!" % service)
    if not closed and not check_result:
        raise AssertionError("Service %s must be work but it doesn't work!" % service)


@step(r'I (\w+) service ([\w\d]+) in ([\w\d]+)')
def service_control(step, action, service, serv_as):
    LOG.info("%s service %s" % (action.title(), service))
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('/etc/init.d/%s %s' % (service, action))


@step('scalarizr version is last in (.+)$')
def assert_scalarizr_version(step, serv_as):
    #TODO: Rewrite this and verify scalarizr version with our repository
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    installed_version = None
    candidate_version = None
    if 'ubuntu' in server.role.os.lower():
        LOG.info('Check ubuntu installed scalarizr')
        out = node.run('apt-cache policy scalarizr-base')
        LOG.debug('Installed information: %s' % out[0])
        for line in out[0].splitlines():
            if line.strip().startswith('Installed'):
                installed_version = line.split()[-1].split('-')[0].split('.')[-1]
                LOG.info('Installed version: %s' % installed_version)
            elif line.strip().startswith('Candidate'):
                candidate_version = line.split()[-1].split('-')[0].split('.')[-1]
                LOG.info('Candidate version: %s' % candidate_version)
    elif ('centos' or 'redhat') in server.role.os.lower():
        LOG.info('Check ubuntu installed scalarizr')
        out = node.run('yum list --showduplicates scalarizr-base')
        LOG.debug('Installed information: %s' % out[0])
        for line in out[0]:
            if line.strip().endswith('installed'):
                installed_version = [word for word in line.split() if word.strip()][1].split('-')[0].split('.')[-1]
                LOG.info('Installed version: %s' % installed_version)
            elif line.strip().startswith('scalarizr-base'):
                candidate_version = [word for word in line.split() if word.strip()][1].split('-')[0].split('.')[-1]
                LOG.info('Candidate version: %s' % candidate_version)
    if candidate_version and not installed_version == candidate_version:
        raise AssertionError('Installed scalarizr is not last! Installed: %s, '
                             'candidate: %s' % (installed_version, candidate_version))


@step('I reboot scalarizr in (.+)$')
def reboot_scalarizr(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('/etc/init.d/scalarizr restart')
    LOG.info('Scalarizr restart complete')


@step("see 'Scalarizr terminated' in ([\w]+) log")
def check_log(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Check scalarizr log for  termination')
    wait_until(world.check_text_in_scalarizr_log, timeout=300, args=(node, "Scalarizr terminated"),
               error_text='Not see "Scalarizr terminated" in debug log')


@step('I ([\w\d]+) service ([\w\d]+)(?: and changed ([\w]+))? on ([\w\d]+)(?: by ([\w]+))?')
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
            service.update({'node': common_config.get(consts.Dist.get_os_family(node.os[0])).get('service_name')})
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
        LOG.error('Service change status info: {0} Service change status error: {1}'.format(res['info'][0], res['info'][1])
        if not is_api
        else 'Status of the process has not changed, pid have not changed. pib before: %s pid after: %s' % (res['pid_before'], res['pid_after']))
        raise AssertionError("Can't {0} service. No such process {1}".format(status_as, service['node']))

    LOG.info('Service change status info: {0}'.format(res['info'][0] if not is_api
        else '%s.%s() complete successfully' % (service['api'], status)))
    LOG.info("Service status was successfully changed : {0} {1} {2}".format(service['node'], status_as,
                                                                            'by api call' if is_api else ''))