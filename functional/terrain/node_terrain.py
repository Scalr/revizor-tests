__author__ = 'gigimon'
import os
import time
import socket
import urllib2
import logging
from datetime import datetime

from lettuce import world, step
import requests

from revizor2 import consts
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.cloud import Cloud
from revizor2.defaults import DEFAULT_SERVICES_CONFIG
from revizor2.consts import Platform, SERVICES_PORTS_MAP


LOG = logging.getLogger(__name__)


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


@step('hostname in ([\w\d]+) is valid')
def verify_hostname_is_valid(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    hostname = node.run('hostname')[0].strip()
    valid_hostname = '%s-%s-%s'.lower() % (world.farm.name.replace(' ', ''), server.role.name, server.index)
    if not hostname == valid_hostname:
        raise AssertionError('Hostname in server %s is not valid: %s (%s)' % (server.id, valid_hostname, hostname))


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
def verify_open_port(step, port, has_not, serv_as):
    server = getattr(world, serv_as)
    port = int(port)
    node = world.cloud.get_node(server)
    if not CONF.feature.dist.startswith('win'):
        for attempt in range(5):
            LOG.info('Add iptables rule for my IP and port %s' % port)
            try:
                my_ip = requests.get('http://ifconfig.me/ip').text.strip()
                break
            except requests.ConnectionError:
                time.sleep(5)
        LOG.info('My IP address: %s' % my_ip)
        node.run('iptables -I INPUT -p tcp -s %s --dport %s -j ACCEPT' % (my_ip, port))
    if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        new_port = world.cloud.open_port(node, port, ip=server.public_ip)
    else:
        new_port = port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    try:
        s.connect((server.public_ip, new_port))
    except (socket.error, socket.timeout), e:
        if has_not:
            LOG.info("Post %s closed" % new_port)
            return
        raise AssertionError(e)
    if has_not:
        raise AssertionError("Port %s is open but must be closed" % new_port)
    LOG.info("Post %s is open" % new_port)


@step(r'([\w-]+) is( not)? running on (.+)')
def assert_check_service(step, service, has_not, serv_as):
    #TODO: Maybe delete this and use only verify_open_port?
    LOG.info("Check service %s" % service)
    has_not = has_not and True or False
    server = getattr(world, serv_as)
    port = SERVICES_PORTS_MAP[service]
    if isinstance(port, (list, tuple)):
        port = port[0]
    if CONF.feature.driver.current_cloud in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        node = world.cloud.get_node(server)
        new_port = world.cloud.open_port(node, port, ip=server.public_ip)
    else:
        new_port = port

    # check if redis/memcached behavior in role behaviors
    if {'redis', 'memcached'}.intersection(server.role.behaviors):
        world.set_iptables_rule(server, SERVICES_PORTS_MAP[service])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    try:
        s.connect((server.public_ip, new_port))
    except (socket.error, socket.timeout), e:
        if not has_not:
            raise AssertionError(e)
        else:
            LOG.info("Service stoped")
    if service == 'redis' and not has_not:
        LOG.info('Set main redis instances to %s' % serv_as)
        setattr(world, 'redis_instances', {6379: world.farm.db_info('redis')['access']['password'].split()[2][:-4]})
    if not has_not:
        LOG.info("Service work")


@step(r'I (\w+) service ([\w\d]+) in ([\w\d]+)')
def service_control(step, action, service, serv_as):
    LOG.info("%s service %s" % (action.title(), service))
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.run('/etc/init.d/%s %s' % (service, action))


@step('not ERROR in ([\w]+) scalarizr log$')
def check_scalarizr_log(step, serv_as):
    """Check scalarizr log for errors"""
    node = world.cloud.get_node(getattr(world, serv_as))
    out = node.run('cat /var/log/scalarizr_debug.log | grep ERROR')[0]
    LOG.info('Check scalarizr error')
    errors = []
    if 'Caught exception reading instance data' in out:
        return
    if 'ERROR' in out:
        log = out.splitlines()
        for l in log:
            try:
                d = datetime.strptime(l.split()[0], '%Y-%m-%d')
                log_level = l.strip().split()[3]
            except ValueError:
                continue
            now = datetime.now()
            if not d.year == now.year or not d.month == now.month or not d.day == now.day or not log_level == 'ERROR':
                continue
            errors.append(l)
    if errors:
        raise AssertionError('ERROR in log: %s' % errors)


@step('scalarizr process is (.+) in (.+)$')
def check_processes(step, count, serv_as):
    time.sleep(60)
    serv = getattr(world, serv_as)
    cl = Cloud()
    node = cl.get_node(serv)
    list_proc = node.run('ps aux | grep scalarizr')[0]
    c = 0
    for pr in list_proc.splitlines():
        if 'bin/scalarizr' in pr:
            c += 1
    LOG.info('Scalarizr count of processes %s' % c)
    world.assert_not_equal(c, int(count), 'Scalarizr processes is: %s but processes \n%s' % (c, list_proc))


@step('scalarizr version is last in (.+)$')
def assert_scalarizr_version(step, serv_as):
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

    LOG.info('Service change status info: {0}'.format(res['info'][0]
    if not is_api
    else '%s.%s() complete successfully' % (service['api'], status)))
    LOG.info("Service status was successfully changed : {0} {1} {2}".format(service['node'], status_as, 'by api call' if is_api else ''))