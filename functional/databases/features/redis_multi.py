import os
import re
import time
import logging

import redis

from lettuce import step, world

from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.dbmsr import Database

LOG = logging.getLogger(__name__)



@step(r'I add (.+) role to this farm with (\d+) redis processes$')
def add_role_to_given_farm(step, role_type, redis_count):
	LOG.info("Add role to farm")
	engine = CONF.main.storage
	LOG.info('Use storage engine: %s' % engine)
	world.role_type = role_type
	options_list = {'eph':{'db.msr.data_storage.engine': 'eph',
	                       'db.msr.data_storage.eph.disk': '/dev/sda2',
	                       'aws.instance_type':'m1.small',
	                       'aws.use_ebs': '0'},
	                'lvm':{'db.msr.data_storage.engine': 'lvm',
	                       'aws.instance_type':'m1.large',
	                       'db.msr.data_storage.fstype': 'ext3',
	                       'db.msr.data_storage.eph.disk': '/dev/sdb'},
	                'raid10':{'db.msr.data_storage.engine': 'raid.ebs',
	                          'db.msr.data_storage.raid.level': '10',
	                          'db.msr.data_storage.raid.volume_size': '15',
	                          'db.msr.data_storage.raid.volumes_count': '8',
	                          'db.msr.data_storage.fstype': 'ext3',
	                          },
	                'raid5':{'db.msr.data_storage.engine': 'raid.ebs',
	                         'db.msr.data_storage.raid.level': '5',
	                         'db.msr.data_storage.raid.volume_size': '1',
	                         'db.msr.data_storage.raid.volumes_count': '3',},
	                'raid0':{'db.msr.data_storage.engine': 'raid.ebs',
	                         'db.msr.data_storage.raid.level': '0',
	                         'db.msr.data_storage.raid.volume_size': '1',
	                         'db.msr.data_storage.raid.volumes_count': '2',},
	                'raid1':{'db.msr.data_storage.engine': 'raid.ebs',
	                         'db.msr.data_storage.raid.level': '1',
	                         'db.msr.data_storage.raid.volume_size': '1',
	                         'db.msr.data_storage.raid.volumes_count': '2',},
	                'ebs':{'db.msr.data_storage.engine':'ebs',
	                       'db.msr.data_storage.ebs.size': '1',}}
	scripting = []
	if CONF.main.platform == 'ec2':
		if role_type == 'mysql':
			options = {'mysql.data_storage_engine' : 'ebs',
			           'mysql.ebs_volume_size'	: 1}
		else:
			options = options_list[engine]
	else:
		options = {}
	options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
	                'db.msr.redis.num_processes': int(redis_count)})
	world.role_options = options
	world.role_scripting = scripting
	role = world.add_role_to_farm(world.role_type, options=options, scripting=scripting)
	setattr(world, world.role_type + '_role', role)
	LOG.info("Set DB object to world")
	if role_type in ['mysql', 'postgresql', 'redis', 'mongodb', 'percona', 'mysql2', 'percona2']:
		db = Database.create(role)
		if not db:
			raise AssertionError('Database for role %s not found!' % role)
		setattr(world, 'db', db)


@step('redis work in ports: ([,\d]+) in (\w+)$')
def get_redis_ports(step, ports, serv_as):
	server = getattr(world, serv_as)
	ports = [int(p) for p in ports.split(',')]
	c = Cloud()
	node = c.get_node(server)
	out = node.run('netstat -ap | grep redis-server')
	server_ports =  [int(port.split()[3].split(':')[1]) for port in out[0].splitlines() if port.split()[3].startswith('*')]
	LOG.debug('Redis ports in server: %s' % server_ports)
	if len(server_ports) == len(ports):
		for p in ports:
			if not p in server_ports:
				raise AssertionError('Redis on port %s not running in server %s' % (p, server.id))
	else:
		raise AssertionError('Count of running redis instances invalid, must be: %s, but: %s (%s)' % (len(ports), len(server_ports), server_ports))


@step('redis instances in ([\w]+) is ([\w]+)')
def check_instance_types(step, serv_as, inst_type):
	server = getattr(world, serv_as)
	world.db.create_access(server)
	passwords = world.farm.db_info('redis')['password']
	passwords = dict(re.findall(r'([\d]+): ([\w]+)', passwords))
	for port in passwords:
		LOG.info('Check instance type in server %s port %s with password %s' % (server.id, port, passwords[port]))
		r = redis.Redis(host=server.public_ip, port=int(port), password=passwords[port], socket_timeout=5, db=0)
		instance_type = r.info()['role']
		if not inst_type == instance_type:
			raise AssertionError('Redis (%s) in server %s is not %s, it %s' % (port, server.id, inst_type, instance_type))


@step('I ([\w]+) data (?:to|from) redis on port ([\d]+) in ([\w]+)')
def action_on_redis(step, action, port, serv_as):
	server = getattr(world, serv_as)
	world.db.create_access(server)
	passwords = world.farm.db_info('redis')['password']
	passwords = dict(re.findall(r'([\d]+): ([\w]+)', passwords))
	r = redis.Redis(host=server.public_ip, port=int(port), password=passwords[port], socket_timeout=5, db=0)
	if action == 'write':
		LOG.info('Insert test key to %s:%s' % (server.public_ip, int(port)))
		r.set('test_key', 'test_value')
	elif action == 'read':
		LOG.info('Read test key from %s:%s' % (server.public_ip, int(port)))
		data = r.get('test_key')
		if not data == 'test_value':
			LOG.error('Receive bad key value from redis instance: %s:%s' % (server.public_ip, int(port)))
			raise AssertionError('Receive bad key value from redis instance: %s:%s' % (server.public_ip, int(port)))


@step('I (?:terminate|stop) farm and store passwords')
def farm_terminate(step):
	"""Terminate (stopping) farm and save redis keys"""
	passwords = world.farm.db_info('redis')['password']
	passwords = dict(re.findall(r'([\d]+): ([\w]+)', passwords))
	world.redis_passwords = passwords
	world.farm.terminate()
	time.sleep(30)


@step('old passwords work in ([\w\d]+)$')
def check_old_passwords(step, serv_as):
	server = getattr(world, serv_as)
	world.db.create_access(server)
	passwords = getattr(world, 'redis_passwords', {})
	for port in passwords:
		LOG.info('Check password for redis instance in server %s port %s with password %s' % (server.id, port, passwords[port]))
		r = redis.Redis(host=server.public_ip, port=int(port), password=passwords[port], socket_timeout=5, db=0)