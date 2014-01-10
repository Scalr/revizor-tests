__author__ = 'gigimon'
import os
import re
import json
import time
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.dbmsr import Database
from revizor2.consts import Platform
from revizor2.api import Script, Farm


LOG = logging.getLogger(__name__)


FARM_OPTIONS = {
    'chef': {
        "chef.bootstrap": 1,
        "chef.runlist": json.dumps(["recipe[memcached::default]"]),
        "chef.attributes": json.dumps({"memcached": {"memory": "1024"}}),
        "chef.server_id": "3",
        "chef.environment": "_default",
        "chef.daemonize": 1,
        },
    'chef-solo': {
        "chef.bootstrap": 1,
        "chef.cookbook_url": "git@github.com:Scalr/int-cookbooks.git",
        "chef.runlist": json.dumps(["recipe[revizor-chef::default]"]),
        "chef.cookbook_url_type": "git",
        "chef.relative_path": "cookbooks",
        "chef.ssh_private_key": open(os.path.expanduser(CONF.main.private_key), 'r').read(),
        "chef.attributes": ""
    },
    'deploy': {
        "dm.application_id": "217",
        "dm.remote_path": "/var/www",
        },
    'winchef': {
        "chef.bootstrap": 1,
        "chef.daemonize": "0",
        "chef.environment": "_default",
        "chef.runlist": json.dumps(["recipe[windows_file_create::default]"]),
        "chef.server_id": "3",
        },
    'branch_stable': {
        "user-data.scm_branch": "release/stable"
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
            "db.msr.data_storage.cinder.size": "1",
            }
    },
    'ecs': {
        'persistent': {
            "db.msr.data_storage.engine": "cinder",
            "db.msr.data_storage.fstype": "ext3",
            "db.msr.data_storage.cinder.size": "1",
            }
    }
}


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_running_farm()


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
    """Clear all roles from farm and stop farm"""
    world.farm = farm = Farm.get(CONF.main.farm_id)
    IMPL.farm.clear_roles(world.farm.id)
    LOG.info('Clear farm')
    if farm.running:
        LOG.info('Terminate farm')
        farm.terminate()


@step(r"I add(?P<behavior> \w+)? role to this farm(?: with (?P<options>[\w\d, -]+))?")
def add_role_to_farm(step, behavior=None, options=None):
    additional_storages = None
    scripting = None
    farm_options = {
        "base.hostname_format": "{SCALR_FARM_NAME}-{SCALR_ROLE_NAME}-{SCALR_INSTANCE_INDEX}"
    }
    if not behavior:
        behavior = os.environ.get('RV_BEHAVIOR', 'base')
    else:
        behavior = behavior.strip()
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
                                 "params": {},
                                 "target": "instance",
                                 "version": "-1",
                                 "timeout": "1200",
                                 "issync": "1",
                                 "order_index": "1",
                                 "event": "HostInit",
                                 "run_as": "root"
                             },
                             {
                                 "script_id": script_id,
                                 "script": "Linux ping-pong",
                                 "params": {},
                                 "target": "instance",
                                 "version": "-1",
                                 "timeout": "1200",
                                 "issync": "1",
                                 "order_index": "10",
                                 "event": "BeforeHostUp",
                                 "run_as": "revizor"
                             },
                             {
                                 "script_id": script_id,
                                 "script": "Linux ping-pong",
                                 "params": {},
                                 "target": "instance",
                                 "version": "-1",
                                 "timeout": "1200",
                                 "issync": "1",
                                 "order_index": "20",
                                 "event": "HostUp",
                                 "run_as": "ubuntu"
                             }]
            elif opt == 'storages':
                LOG.info('Add additional storages')
                if CONF.feature.driver.current_cloud in [Platform.EC2]:
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
                elif CONF.feature.driver.current_cloud in [Platform.IDCF, Platform.CLOUDSTACK]:
                    LOG.info('Add storages from IDCF/CloudStack')
                    additional_storages = {
                        "configs": [{
                                        "id": None,
                                        "type": "csvol",
                                        "fs": "ext3",
                                        "settings": {
                                            "csvol.size": "1",
                                            },
                                        "mount": True,
                                        "mountPoint": "/media/ebsmount",
                                        "reUse": True,
                                        "status": "",
                                        }, {
                                        "id": None,
                                        "type": "raid.csvol",
                                        "fs": "ext3",
                                        "settings": {
                                            "raid.level": "10",
                                            "raid.volumes_count": 4,
                                            "csvol.size": "1",
                                            },
                                        "mount": True,
                                        "mountPoint": "/media/raidmount",
                                        "reUse": True,
                                        "status": "",
                                        }]
                    }
                elif CONF.feature.driver.current_cloud in [Platform.OPENSTACK, Platform.ECS]:
                    LOG.info('Add storages from OpenStack')
                    additional_storages = {
                        "configs": [{
                                        "id": None,
                                        "type": "cinder",
                                        "fs": "ext3",
                                        "settings": {
                                            "cinder.size": "1"
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
                                            "cinder.size": "1"
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
    if behavior == 'rabbitmq':
        del(farm_options['base.hostname_format'])
    if behavior == 'tomcat6' and CONF.feature.dist.startswith('ubuntu'):
        behavior = 'tomcat7'
    if behavior == 'redis':
        LOG.info('Add redis settings')
        farm_options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                             'db.msr.redis.use_password': True})
    if behavior in ['mysql', 'mysql2', 'percona2', 'mariadb', 'postgresql', 'redis', 'mongodb', 'percona']:
        storage = STORAGES.get(CONF.feature.driver.cloud_family, None)
        if storage:
            LOG.info('Add main settings for %s storage' % CONF.feature.storage)
            farm_options.update(storage.get(CONF.feature.storage, {}))
    world.role_options = farm_options
    world.role_scripting = scripting
    LOG.debug('All farm settings: %s' % farm_options)
    role = world.add_role_to_farm(behavior, options=farm_options, scripting=scripting, storages=additional_storages)
    setattr(world, '%s_role' % behavior, role)
    world.role = role
    if behavior in ['mysql', 'postgresql', 'redis', 'mongodb', 'percona', 'mysql2', 'percona2', 'mariadb']:
        db = Database.create(role)
        if not db:
            raise AssertionError('Database for role %s not found!' % role)
        world.database_users = {}
        world.db = db


@step('I delete (\w+) role from this farm')
def delete_role_from_farm(step, role_type):
    LOG.info('Delete role %s from farm' % role_type)
    role = getattr(world, '%s_role' % role_type)
    world.farm.delete_role(role.role_id)


@step('I (?:terminate|stop) farm')
def farm_terminate(step):
    """Terminate (stopping) farm"""
    world.farm.terminate()
    time.sleep(30)


@step('I start farm$')
def farm_launch(step):
    """Start farm"""
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I start farm with delay$')
def farm_launch(step):
    """Start farm with delay for cloudstack"""
    if CONF.feature.driver.current_cloud in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))