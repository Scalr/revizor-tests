import os
import time
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.api import Script


LOG = logging.getLogger('scripting')


@step('I add role to this farm with scripts attached')
def having_role_in_farm(step):
	role_type = os.environ.get('RV_BEHAVIOR', 'base')
	script_id = Script.get_id('Linux ping-pong')['id']
	role = world.add_role_to_farm(role_type=role_type,
	                              scripting=[
		                              {
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
		                              },
	                              ])
	LOG.info('Add role to farm %s' % role)
	world.role_type = role_type
	if not role:
		raise AssertionError('Error in add role to farm')
	setattr(world, world.role_type + '_role', role)
	world.role = role


@step("([\w]+) script executed scalarizr is in '(.+)' state in (.+)")
def assert_check_script(step, message, state, serv_as):
	serv = getattr(world, serv_as)
	wait_until(world.wait_script_execute, args=(serv, message, state), timeout=600,
	           error_text='I\'m not see %s scripts execution for server %s' % (message, serv.id))


@step("([\w]+) event in script log for (.+)")
def assert_check_script_in_log(step, message, serv_as):
	time.sleep(10)
	serv = getattr(world, serv_as)
	serv.scriptlogs.reload()
	for log in serv.scriptlogs:
		LOG.debug('Check script log: %s' % log.message)
		if log.event.strip() == message.strip():
			return True
	raise AssertionError('I\'m not see %s in script logs for server %s' % (message, serv.id))


@step('I see script result in (.+)')
def assert_check_script_work(step, serv_as):
	time.sleep(15)
	serv = getattr(world, serv_as)
	serv.scriptlogs.reload()
	last_count = getattr(world, '%s_script_count' % serv_as)
	if not len(serv.scriptlogs) == last_count+1:
		LOG.warning('Last count of script logs: %s, new: %s' % (last_count, len(serv.scriptlogs)))
		raise AssertionError('Not see script result in script logs')
