import os
from datetime import datetime


from lettuce import world, step, after, before
from common import *

import paramiko

from revizor2.conf import CONF
from revizor2.api import Script
from revizor2.backend import IMPL
from revizor2.utils import wait_until
from revizor2.cloud import Cloud
from revizor2.cloud.node import ExtendedNode
from revizor2.consts import ServerStatus
from revizor2.dbmsr import Database
from revizor2.consts import Platform


PORTS_MAP = {'mysql': 3306, 'mysql2': 3306, 'mariadb': 3306, 'percona':3306, 'postgresql': 5432, 'redis': (6379,6395),
             'mongodb': 27018, 'mysqlproxy': 4040, 'scalarizr': 8013, 'scalr-upd-client': 8008, 'nginx': 80,
             'apache': 80, 'memcached' : 11211}


FARM_OPTIONS = {
    'chef': {
        "chef.bootstrap": 1,
        "chef.runlist_id": "143",
        "chef.attributes": '{"memcached":{"memory":"1024"}}',
        "chef.server_id": "3",
        "chef.environment": "_default",
        "chef.role_name": None,
        "chef.node_name_tpl": "",
    },
    'deploy': {
        "dm.application_id": "217",
        "dm.remote_path": "/var/www",
    },
    'winchef': {
        "chef.bootstrap": "1",
        "chef.daemonize": "0",
        "chef.environment": "_default",
        "chef.runlist_id": "189",
        "chef.server_id": "3",
        "chef.role_name": None,
        "chef.node_name_tpl": "",
    }
}


STORAGES = {
    'ec2': {
        'persistent': {
            'db.msr.data_storage.engine': 'ebs',
            'db.msr.data_storage.ebs.size': '1'
        },
        'lvm': {
            'db.msr.data_storage.engine': 'lvm',
            'aws.instance_type': 'm1.small',
            'db.msr.data_storage.fstype': 'ext3',
            'db.msr.storage.lvm.volumes': '{"ephemeral0":"150"}',
            'db.msr.data_storage.eph.disk': '/dev/sda2'
        },
        'eph': {
            'db.msr.data_storage.engine': 'eph',
            'db.msr.data_storage.eph.disk': '/dev/sda2',
            'aws.instance_type': 'm1.small',
            'aws.use_ebs': '0'
        },
        'raid10': {
            'db.msr.data_storage.engine': 'raid.ebs',
            'db.msr.data_storage.raid.level': '10',
            'db.msr.data_storage.raid.volume_size': '1',
            'db.msr.data_storage.raid.volumes_count': '4'
        },
        'raid5': {
            'db.msr.data_storage.engine': 'raid.ebs',
            'db.msr.data_storage.raid.level': '5',
            'db.msr.data_storage.raid.volume_size': '1',
            'db.msr.data_storage.raid.volumes_count': '3'
        },
        'raid0': {
            'db.msr.data_storage.engine': 'raid.ebs',
            'db.msr.data_storage.raid.level': '0',
            'db.msr.data_storage.raid.volume_size': '1',
            'db.msr.data_storage.raid.volumes_count': '2'
        },
        'raid1': {
            'db.msr.data_storage.engine': 'raid.ebs',
            'db.msr.data_storage.raid.level': '1',
            'db.msr.data_storage.raid.volume_size': '1',
            'db.msr.data_storage.raid.volumes_count': '2'
        },
    },
    'rackspaceng': {
        'persistent': {
            'db.msr.data_storage.engine': 'cinder',
            'db.msr.data_storage.cinder.size': '100',
            'db.msr.data_storage.fstype': 'ext3',
        },
        'lvm': {
            'db.msr.data_storage.engine': 'lvm',
            'db.msr.data_storage.fstype': 'ext3',
            'db.msr.data_storage.cinder.size': '1',
        },
        'eph': {
            'db.msr.data_storage.engine': 'eph',
            'db.msr.data_storage.fstype': 'ext3',
            'db.msr.data_storage.eph.disk': '/dev/loop0',
        }
    },
    'gce': {
        'persistent': {
            'db.msr.data_storage.engine': 'gce_persistent',
            'db.msr.data_storage.gced.size': '1',
            'db.msr.data_storage.fstype': 'ext3'
        },
        'lvm': {
            'db.msr.data_storage.engine': 'lvm',
            'db.msr.data_storage.fstype': 'ext3',
            'db.msr.data_storage.eph.disk': 'ephemeral-disk-0',
            'db.msr.storage.lvm.volumes': '{"google-ephemeral-disk-0":420}'
        },
        'eph': {
            'db.msr.data_storage.engine': 'eph',
            'db.msr.data_storage.eph.disk': 'ephemeral-disk-0',
            'db.msr.data_storage.fstype': 'ext3',
        }
    },
    'openstack': {
        'persistent': {
            "db.msr.data_storage.engine": "cinder",
            "db.msr.data_storage.fstype": "ext3",
            "db.msr.data_storage.cinder.size": "100",
        }
    }
}


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_running_farm()


@step(r"I add(?P<behavior> \w+)? role to this farm(?: with (?P<options>[\w\d, ]+))?")
def add_role_to_farm(step, behavior=None, options=None):
    additional_storages = None
    scripting = None
    farm_options = {}
    if not behavior:
        behavior = os.environ.get('RV_BEHAVIOR', 'base')
    else:
        behavior = behavior.strip()
    if behavior == 'tomcat6' and CONF.main.dist.startswith('ubuntu'):
        behavior = 'tomcat7'
    options = options.strip() if options else None
    if options:
        for opt in [o.strip() for o in options.strip().split(',')]:
            LOG.info('Inspect option: %s' % opt)
            if 'redis processes' in opt:
                LOG.info('Add redis processes')
                redis_count = re.findall(r'(\d+) redis processes', options)[0].strip()
                farm_options.update({'db.msr.redis.num_processes': int(redis_count)})
            elif opt == 'scripts':
                LOG.info('Add scripting')
                script_id = Script.get_id('Linux ping-pong')['id']
                scripting = [{
                                "script_id": script_id,
                                "script": "Linux ping-pong",
                                "params": [],
                                "target": "instance",
                                "version": "-1",
                                "timeout": "1200",
                                "issync": "1",
                                "order_index": "1",
                                "event": "HostInit"
                            },
                            {
                                "script_id": script_id,
                                "script": "Linux ping-pong",
                                "params": [],
                                "target": "instance",
                                "version": "-1",
                                "timeout": "1200",
                                "issync": "1",
                                "order_index": "10",
                                "event": "BeforeHostUp"
                            },
                            {
                                "script_id": script_id,
                                "script": "Linux ping-pong",
                                "params": [],
                                "target": "instance",
                                "version": "-1",
                                "timeout": "1200",
                                "issync": "1",
                                "order_index": "20",
                                "event": "HostUp"
                            }]
            elif opt == 'storages':
                LOG.info('Add additional storages')
                if CONF.main.driver in [Platform.EC2]:
                    LOG.info('Add storages from EC2')
                    additional_storages = {
                            "configs": [{
                                    "id": None,
                                    "type": "ebs",
                                    "fs": "ext3",
                                    "settings": {
                                            "ebs.size": "1",
                                            "ebs.type": "standard",
                                            "ebs.snapshot": None,
                                    },
                                    "mount": True,
                                    "mountPoint": "/media/ebsmount",
                                    "reUse": True,
                                    "status": "",
                            }, {
                                    "id": None,
                                    "type": "raid.ebs",
                                    "fs": "ext3",
                                    "settings": {
                                            "raid.level": "10",
                                            "raid.volumes_count": 4,
                                            "ebs.size": "1",
                                            "ebs.type": "standard",
                                            "ebs.snapshot": None,
                                    },
                                    "mount": True,
                                    "mountPoint": "/media/raidmount",
                                    "reUse": True,
                                    "status": "",
                            }]
                    }
                # elif CONF.main.driver in [Platform.IDCF, Platform.CLOUDSTACK]:
                #     LOG.info('Add storages from IDCF/CloudStack')
                #     additional_storages = {
                #             "configs": [{
                #                     "id": None,
                #                     "type": "csvol",
                #                     "fs": "ext3",
                #                     "settings": {
                #                             "csvol.size": "1",
                #                     },
                #                     "mount": True,
                #                     "mountPoint": "/media/ebsmount",
                #                     "reUse": True,
                #                     "status": "",
                #             }, {
                #                     "id": None,
                #                     "type": "raid.csvol",
                #                     "fs": "ext3",
                #                     "settings": {
                #                             "raid.level": "10",
                #                             "raid.volumes_count": 4,
                #                             "csvol.size": "1",
                #                     },
                #                     "mount": True,
                #                     "mountPoint": "/media/raidmount",
                #                     "reUse": True,
                #                     "status": "",
                #             }]
                #     }
                elif CONF.main.driver in [Platform.OPENSTACK, Platform.ENTERIT]:
                    LOG.info('Add storages from OpenStack')
                    additional_storages = {
                        "configs": [{
                                        "id": None,
                                        "type": "cinder",
                                        "fs": "ext3",
                                        "settings": {
                                            "cinder.size": "100"
                                        },
                                        "mount": True,
                                        "mountPoint": "/media/ebsmount",
                                        "reUse": True,
                                        "status": "",
                                        "rebuild": False
                                    }, {
                                        "id": None,
                                        "type": "raid.cinder",
                                        "fs": "ext3",
                                        "settings": {
                                            "raid.level": "10",
                                            "raid.volumes_count": 4,
                                            "cinder.size": "100"
                                        },
                                        "mount": True,
                                        "mountPoint": "/media/raidmount",
                                        "reUse": True,
                                        "status": "",
                                        "rebuild": False
                                    }]
                    }
            else:
                LOG.info('Add %s' % opt)
                farm_options.update(FARM_OPTIONS.get(opt, {}))
    if behavior == 'redis':
        LOG.info('Add redis settings')
        farm_options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                             'db.msr.redis.use_password': True})
    if behavior in ['mysql', 'postgresql', 'redis', 'mongodb', 'percona', 'mysql2', 'percona2', 'mariadb']:
        storage = STORAGES.get(Platform.to_scalr(CONF.main.driver), None)
        if storage:
            LOG.info('Add main settings for %s storage' % CONF.main.storage)
            farm_options.update(storage.get(CONF.main.storage, {}))
    world.role_type = behavior
    world.role_options = farm_options
    world.role_scripting = scripting
    LOG.debug('All farm settings: %s' % farm_options)
    role = world.add_role_to_farm(world.role_type, options=farm_options, scripting=scripting, storages=additional_storages)
    setattr(world, '%s_role' % world.role_type, role)
    world.role = role
    if behavior in ['mysql', 'postgresql', 'redis', 'mongodb', 'percona', 'mysql2', 'percona2', 'mariadb']:
        db = Database.create(role)
        if not db:
            raise AssertionError('Database for role %s not found!' % role)
        setattr(world, 'db', db)


@step('I delete (\w+) role from this farm')
def delete_role_from_farm(step, role_type):
    LOG.info('Delete role %s from farm' % role_type)
    role = getattr(world, '%s_role' % role_type)
    world.farm.delete_role(role.role_id)


@step('I expect server bootstrapping as ([\w\d]+)$')
def expect_server_bootstraping(step, serv_as, timeout=2000):
    """Bootstrap server and add it to world"""
    spec = 'running'
    role = getattr(world, world.role_type + '_role', None)
    if role is None:
        role = world.farm.roles()[0]
    server = wait_until(world.check_server_status, args=(spec, role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    setattr(world, serv_as, server)


@step('I expect server bootstrapping as (.+) in (.+) role$')
def expect_server_bootstraping_for_role(step, serv_as, role_type, timeout=2000):
    """Expect server bootstrapping to 'Running' and check every 10 seconds scalarizr log for ERRORs and Traceback"""
    spec = 'running'
    role = getattr(world, '%s_role' % role_type)
    server = wait_until(check_server_status, args=(spec, role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    setattr(world, serv_as, server)


@step(r'I terminate server ([\w]+)$')
def terminate_server(step, serv):
    """Terminate server (no force)"""
    server = getattr(world, serv)
    LOG.info('Terminate server %s' % server.id)
    server.terminate()


@step(r'I terminate server ([\w]+) with decrease')
def terminate_server_decrease(step, serv):
    """Terminate server (no force), but with decrease"""
    server = getattr(world, serv)
    LOG.info('Terminate server %s with decrease' % server.id)
    server.terminate(decrease=True)


@step('I force terminate ([\w\d]+)$')
def terminate_server_force(step, serv_as):
    """Terminate server force"""
    server = getattr(world, serv_as)
    LOG.info('Terminate server %s force' % server.id)
    server.terminate(force=True)


@step('I force terminate server ([\w\d]+) with decrease$')
def terminate_server_force(step, serv_as):
    """Terminate server force"""
    server = getattr(world, serv_as)
    LOG.info('Terminate server %s force' % server.id)
    server.terminate(force=True, decrease=True)


@step('I reboot server (.+)$')
def reboot_server(step, serv_as):
    #TODO: Delete this
    if CONF.main.driver == Platform.GCE:
        return
    server = getattr(world, serv_as)
    server.reboot()
    LOG.info('Server %s was rebooted' % serv_as)


@step('I increase minimum servers to (.+) for (.+) role')
def increase_instances(step, count, role_type):
    """Increase minimum servers count for role"""
    role = getattr(world, '%s_role' % role_type)
    options = {"scaling.max_instances": int(count) + 1,
                    "scaling.min_instances": count}
    world.farm.edit_role(role.role_id, options)


@step('Scalr ([^ .]+) ([^ .]+) (?:to|from) ([^ .]+)')
def assert_get_message(step, msgtype, msg, serv_as, timeout=1500):
    """Check scalr in/out message delivering"""
    LOG.info('Check message %s %s server %s' % (msg, msgtype, serv_as))
    if CONF.main.driver == Platform.GCE and msg in ['RebootStart', 'RebootFinish']:
        return
    try:
        LOG.info('Check message in server %s' % serv_as)
        server = getattr(world, serv_as)
        wait_until(world.check_message_status, args=(msg.strip(), server, msgtype), timeout=timeout, error_text="I'm not see this %s state in server" % msg)
    except AttributeError:
        LOG.info('Find messages in all servers')
        server = world.db.get_servers()
        LOG.debug('Check message in servers %s' % server)
        s = wait_until(world.check_message_in_server_list, args=(msg.strip(), server, msgtype), timeout=timeout, error_text="I'm not see this %s state in server" % msg)
        setattr(world, serv_as, s)


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
    if not CONF.main.dist.startswith('win'):
        LOG.info('Add iptables rule for my IP')
        try:
            my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
        except httplib.BadStatusLine:
            time.sleep(5)
            my_ip = urllib2.urlopen('http://ifconfig.me/ip').read().strip()
        LOG.info('My IP address: %s' % my_ip)
        node.run('iptables -I INPUT -p tcp -s %s --dport %s -j ACCEPT' % (my_ip, port))
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        new_port = world.cloud.open_port(node, port, ip=server.public_ip)
    else:
        new_port = port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    try:
        s.connect((server.public_ip, new_port))
    except (socket.error, socket.timeout), e:
        if has_not:
            LOG.info("Post %s is closed" % new_port)
            return
        raise AssertionError(e)
    if has_not:
        raise AssertionError("Port %s is open but must be closed" % new_port)
    LOG.info("Post %s is open" % new_port)


@step(r'([\w-]+) is running on (.+)')
def assert_check_service(step, service, serv_as):
    LOG.info("Check service %s" % service)
    server = getattr(world, serv_as)
    port = PORTS_MAP[service]
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        node = world.cloud.get_node(server)
        new_port = world.cloud.open_port(node, port, ip=server.public_ip)
    else:
        new_port = port

    if world.role_type in ['redis', 'memcached']:
        world.set_iptables_rule(world.role_type, server, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    try:
        s.connect((server.public_ip, new_port))
    except (socket.error, socket.timeout), e:
        raise AssertionError(e)
    if service == 'redis':
        LOG.info('Set main redis instances to %s' % serv_as)
        setattr(world, 'redis_instances', {6379: world.farm.db_info('redis')['access']['password'].split()[2][:-4]})
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


@step('I know ([\w]+) storages$')
def get_ebs_for_instance(step, serv_as):
    """Give EBS storages for server"""
    #TODO: Add support for rackspaceng
    server = getattr(world, serv_as)
    volumes = server.get_volumes()
    LOG.debug('Volumes for server %s is: %s' % (server.id, volumes))
    if CONF.main.driver == Platform.EC2:
        storages = filter(lambda x: 'sda' not in x.extra['device'], volumes)
    elif CONF.main.driver in [Platform.IDCF, Platform.CLOUDSTACK]:
        storages = filter(lambda x: x.extra['type'] == 'DATADISK', volumes)
    else:
        return
    LOG.info('Storages for server %s is: %s' % (server.id, storages))
    if not storages:
        raise AssertionError('Server %s not have storages (%s)' % (server.id, storages))
    setattr(world, '%s_storages' % serv_as, storages)


@step('([\w]+) storage is (.+)$')
def check_ebs_status(step, serv_as, status):
    """Check EBS storage status"""
    if CONF.main.driver == Platform.GCE:
        return
    time.sleep(30)
    server = getattr(world, serv_as)
    wait_until(world.check_server_storage, args=(serv_as, status), timeout=300, error_text='Volume from server %s is not %s' % (server.id, status))


@step('I create server snapshot for ([\w]+)$')
def rebundle_server(step, serv_as):
    """Start rebundle for server"""
    serv = getattr(world, serv_as)
    name = 'tmp-%s-%s' % (serv.role.name, datetime.now().strftime('%m%d%H%M'))
    bundle_id = serv.create_snapshot('no_replace', name)
    if bundle_id:
        world.bundle_id = bundle_id


@step('Bundle task created for ([\w]+)')
def assert_bundletask_created(step, serv_as):
    """Check bundle task status"""
    serv = getattr(world, serv_as)
    world.bundle_task_created(serv, world.bundle_id)


@step('Bundle task becomes completed for ([\w]+)')
def assert_bundletask_completed(step, serv_as, timeout=1800):
    serv = getattr(world, serv_as)
    wait_until(world.bundle_task_completed, args=(serv, world.bundle_id), timeout=timeout, error_text="Bundle not completed")


@step('I add to farm role created by last bundle task')
def add_new_role_to_farm(step):
    options = getattr(world, 'role_options', {})
    scripting = getattr(world, 'role_scripting', [])
    if world.role_type == 'redis':
        repl_type = os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof')
        options.update({'db.msr.redis.persistence_type': repl_type,})
    world.farm.add_role(world.new_role_id, options=options, scripting=scripting)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, world.role_type + '_role', role)
    LOG.info("Set DB object to world")
    if world.role_type in ['mysql', 'percona', 'postgresql', 'redis', 'mongodb', 'mysql2', 'percona2']:
        db = Database.create(role)
        if db:
            setattr(world, 'db', db)


@step("I execute script '(.+)' (.+) on (.+)")
def execute_script(step, script_name, exec_type, serv_as):
    synchronous = 1 if exec_type.strip() == 'synchronous' else 0
    serv = getattr(world, serv_as)
    script = Script.get_id(script_name)
    LOG.info('Execute script id: %s, name: %s' % (script['id'], script_name))
    serv.scriptlogs.reload()
    setattr(world, '%s_script_count' % serv_as, len(serv.scriptlogs))
    LOG.debug('Count of complete scriptlogs: %s' % len(serv.scriptlogs))
    Script.script_execute(world.farm.id, serv.farm_role_id, serv.id, script['id'], synchronous, script['version'])
    LOG.info('Script execute success')


@step('I (?:terminate|stop) farm')
def farm_terminate(step):
    """Terminate (stopping) farm"""
    world.farm.terminate()
    time.sleep(30)


@step('I wait ([\d]+) minutes')
def wait_time(step, minutes):
    time.sleep(int(minutes)*60)


@step('I start farm$')
def farm_launch(step):
    """Start farm"""
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I start farm with delay$')
def farm_launch(step):
    """Start farm with delay for cloudstack"""
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('wait all servers are terminated')
def wait_all_terminated(step):
    """Wait termination of all servers"""
    wait_until(world.wait_farm_terminated, timeout=1800, error_text='Servers in farm not terminated too long')


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


@before.all
def initialize_world():
    setattr(world, 'test_start_time', datetime.now())
    c = Cloud()
    setattr(world, 'cloud', c)


@after.each_scenario
def get_all_logs(scenario):
    """Give scalarizr_debug.log logs from servers"""
    if CONF.main.dist.startswith('win'):
        return
    LOG.warning('Get scalarizr logs after scenario %s' % scenario.name)
    farm = getattr(world, 'farm', None)
    if not farm:
        return
    farm.servers.reload()
    servers = farm.servers
    test_name = scenario.described_at.file.split('/')[-1].split('.')[0]
    LOG.debug('Test name: %s' % test_name)
    start_time = world.test_start_time
    path = os.path.realpath(os.path.join(CONF.main.logpath, 'scalarizr', test_name,
                                        start_time.strftime('%m%d-%H:%M'), scenario.name.replace('/', '-')))
    LOG.debug('Path to save log: %s' % path)
    if not os.path.exists(path):
        os.makedirs(path, 0755)
    for serv in servers:
        if serv.status == ServerStatus.RUNNING or serv.status == ServerStatus.INIT or serv.status == ServerStatus.PENDING:
            try:
                node = world.cloud.get_node(serv)
                if node:
                    node.sftp_get_file('/var/log/scalarizr_debug.log', os.path.join(path, serv.id + '_scalarizr_debug.log'))
                    LOG.info('Save scalarizr log from server %s' % serv.id)
                    #node.run('echo -n > /var/log/scalarizr_debug.log')
                    #LOG.info('Scalarizr log was cleaned')
                    LOG.info('Compressing /etc/scalr directory')
                    node.run('tar -czf /tmp/scalr.tar.gz /etc/scalr')
                    LOG.info('Download archive with scalr directory')
                    node.sftp_get_file('/tmp/scalr.tar.gz', os.path.join(path, serv.id + '_scalr.tar.gz'))
                    LOG.info('Remove archive')
                    node.run('rm -rf /tmp/scalr.tar.gz')
            except paramiko.AuthenticationException:
                LOG.error('Can\'t authenticated to server: %s for get log' % serv.id)
            except IOError:
                LOG.error('Server %s not have scalarizr_debug.log' % serv.id)
            except BaseException, e:
                LOG.error(e)
                continue


@after.all
def cleanup_all(total):
    """If not have problem - stop farm and delete roles, vhosts, domains"""
    LOG.info('Failed steps: %s' % total.steps_failed)
    LOG.debug('Results %s' % total.scenario_results)
    LOG.debug('Passed %s' % total.scenarios_passed)
    if not total.steps_failed and CONF.main.stop_farm:
        LOG.info('Clear and stop farm...')
        farm = getattr(world, 'farm', None)
        if not farm:
            return
        role = getattr(world, world.role_type + '_role', None)
        if not role:
            IMPL.farm.clear_roles(world.farm.id)
            return
        IMPL.farm.clear_roles(world.farm.id)
        new_role_id = getattr(world, 'new_role_id', None)
        if new_role_id:
            LOG.info('Delete bundled role: %s' % new_role_id)
            try:
                IMPL.role.delete(new_role_id, delete_image=True)
            except:
                pass
        cloud_node = getattr(world, 'cloud_server', None)
        if cloud_node:
            LOG.info('Destroy node in cloud')
            cloud_node.destroy()
        world.farm.terminate()
        world.farm.vhosts.reload()
        world.farm.domains.reload()
        for vhost in world.farm.vhosts:
            LOG.info('Delete vhost: %s' % vhost.name)
            vhost.delete()
        for domain in world.farm.domains:
            LOG.info('Delete domain: %s' % domain.zone_name)
            domain.delete()
    else:
        farm = getattr(world, 'farm', None)
        if not farm:
            return
        world.farm.roles.reload()
        for r in world.farm.roles:
            IMPL.farm.edit_role(world.farm.id, r.role_id, options={"system.timeouts.reboot": 9999,
                                                                   "system.timeouts.launch": 9999})
    for v in dir(world):
        if isinstance(getattr(world, v), ExtendedNode):
            world.__delattr__(v)
