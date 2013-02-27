import re
import time
import logging
import random

import pymongo
from lettuce import world, step

from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.fixtures import resources

LOG = logging.getLogger('mongoshards')


@step('I (add|delete) shard')
def add_shard(step, action):
	world.farm.mongodb_shard(action)
	LOG.info('Add shard in farm %s' % world.farm.id)
	time.sleep(60)


@step('wait ([\d]+) servers is running')
def assert_wait_servers(step, serv_count):
	serv_count = int(serv_count)
	timeout = 60 * 15 * serv_count
	LOG.info('Wait %s servers, timeout %s seconds' % (serv_count, timeout))
	wait_until(world.wait_servers_running, args=(world.mongodb_role.role_id, serv_count), timeout=timeout,
			error_text='Not see %s servers running' % serv_count)


@step('servers \[([\w\d,-]+)\] in replicaset R([\d]+)')
def assert_check_replicaset(step, slaves, serv_ind):
	world.farm.servers.reload()
	server = None
	serv_ind = int(serv_ind) - 1
	for serv in world.farm.servers:
		if serv.status == 'Running' and serv.role_id == world.mongodb_role.role_id:
			if int(serv.cluster_position[0]) == serv_ind:
				server = serv
				LOG.info('Found server %s with cluster position %s' % (server.id, serv.cluster_position))
				break
	world.assert_not_exist(server, 'Not find shard server %s' % serv_ind)
	slaves = slaves.split(',')
	mongo = pymongo.Connection(server.public_ip, 27018, read_preference=pymongo.ReadPreference.SECONDARY)
	mongo.admin.authenticate('scalr', world.farm.db_info('mongodb')['password'])
	members = [member['name'].split('mongo')[1].split(':')[0][1:] for member in mongo.admin.command('replSetGetStatus')['members']]
	LOG.info('Members in replicaset %s are %s' % (serv_ind, ','.join(members)))
	for s in slaves:
		world.assert_not_in(s, members, 'Member %s not in replicaset, all members: %s' % (s, members))


@step('shard status have ([\d]+) replicaset')
def assert_shard_status(step, serv_count):
	serv_count = int(serv_count)
	world.farm.servers.reload()
	server = None
	for serv in world.farm.servers:
		if serv.status == 'Running' and serv.role_id == world.mongodb_role.role_id:
			if serv.cluster_position == '0-0':
				server = serv
				LOG.info('Found server %s with cluster position %s' % (server.id, serv.cluster_position))
				break
	world.assert_not_exist(server, 'Not find server with index 0-0')
	conn = world.db.get_conn(server, 27017)
	LOG.info('Create mongo connection to %s' % server.id)
	cur = conn.config.shards.find()
	rs_list = set([rs['host'].split('/')[0][-1] for rs in cur])
	LOG.info('Get replicaset status and it %s' % rs_list)
	world.assert_not_equal(serv_count, len(rs_list), 'Replicaset count is not equal, see %s, but need %s' % (len(rs_list), serv_count))


@step('I random terminate ([\d]+) servers')
def random_terminates(step, serv_count):
	dead_index = random.sample(range(9), 5)
	servs = []
	for serv in world.farm.servers:
		if serv.status == 'Running' and serv.role_id == world.mongodb_role.role_id:
			servs.append(serv)
	for i in dead_index:
		LOG.info('Terminate server %s' % servs[i].id)
		servs[i].terminate(force=True)


@step('wait cluster status ([\w]+)')
def check_cluster_terminate(step, status):
	wait_until(world.check_mongo_status, args=(status,), timeout=1800,
	           error_text='Mongodb cluster status not %s, is: %s' % (status, world.farm.db_info('mongodb')['status']))