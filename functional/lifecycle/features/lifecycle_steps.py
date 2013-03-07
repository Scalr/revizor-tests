import os
import time
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.api import Farm, Script, IMPL
from revizor2.conf import CONF 
from revizor2.utils import wait_until
from revizor2.consts import ServerStatus
from revizor2.cloud import Cloud


LOG = logging.getLogger('lifecycle')


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
	world.farm = farm = Farm.get(CONF.main.farm_id)
	IMPL.farm.clear_roles(world.farm.id)
	LOG.info('Clear farm')
	if farm.running:
		LOG.info('Terminate farm')
		farm.terminate()


@step('I add role to this farm with deploy')
def having_role_in_farm(step):
	role_type = os.environ.get('RV_BEHAVIOR', 'base')
	role = world.add_role_to_farm(role_type=role_type,
								options={"dm.application_id": "217",
										 "dm.remote_path": "/var/www", })
	LOG.info('Add role to farm %s' % role)
	world.role_type = role_type
	if not role:
		raise AssertionError('Error in add role to farm')
	setattr(world, world.role_type + '_role', role)
	world.role = role


@step('I see (.+) server (.+)$')
def waiting_for_assertion(step, spec, serv_as, timeout=1400):
	if CONF.main.platform == 'ucloud':
		timeout = 2000
	server = wait_until(world.check_server_status, args=(spec, world.role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
	setattr(world, serv_as, server)
	LOG.info('Server succesfull %s' % spec)


@step('I wait and see (.+) server (.+)$')
def waiting_server(step, spec, serv_as, timeout=1400):
	if CONF.main.platform == 'ucloud':
		timeout = 2000
	server = wait_until(world.check_server_status, args=(spec, world.role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
	LOG.info('Server succesfull %s' % spec)
	setattr(world, serv_as, server)


@step('I have (.+) server (.+)$')
def having_server(step, state, serv_as):
	server = getattr(world, serv_as)
	world.assert_not_equal(server.status, ServerStatus.from_code(state), "Server %s is not in state %s" % (server.id, state))


@step("directory '(.+)' exist in (.+)$")
def check_path(step, path, serv_as):
	c = Cloud()
	node = c.get_node(getattr(world, serv_as))
	out = node.run('/bin/ls %s' % path)
	LOG.info('Check directory %s' % path)
	if 'No such file or directory' in out[0] or 'No such file or directory' in out[1]:
		LOG.error('Directory not exist')
		raise AssertionError('No path %s' % path)


# @step('I reboot it')
# def reboot_server(step):
# 	world.server.reboot()
# 	LOG.info('Server reboot')


#@step('Scalr (receives|sends) ([\w]+)$')
#def message_received(step, msgtype, msgname, timeout=1000):
#	msgname = msgname.strip()
#	wait_until(world.check_message_status, args=(msgname, world.server, msgtype), timeout=timeout, error_text="I'm not see message %s in server" % msgname)
#	LOG.info('Scalr %s %s' % (msgtype, msgname))


# @step('I execute on it script (.+)')
# def execute_script_on_server(step, script_name):
# 	LOG.info('Execute script name %s' % script_name)
# 	script = Script.get_id(script_name.strip()[1:-1])
# 	Script.script_execute(world.server.farm_id, world.server.farm_role_id, world.server.id, script['id'], revision=script['version'])
# 	LOG.info('Execute script id %s (%s, %s)' % (script['id'], script['name'], script['version']))
# 	world.server.scriptlogs.reload()
# 	script_log_count = len(world.server.scriptlogs)
# 	LOG.info('Save count scripts log: %s' % script_log_count)
# 	setattr(world, 'server_script_count', script_log_count)


@step('I see execution result in scripting log')
def check_result_script_log(step):
	wait_until(check_script_log, timeout=1000, error_text="I'm not see messages in script logs")


@step("script output contains '(.+)' in (.+)$")
def assert_check_message_in_log(step, message, serv_as):
	time.sleep(60)
	server = getattr(world, serv_as)
	server.scriptlogs.reload()
	for log in server.scriptlogs:
		LOG.debug('Server %s log content: %s' % (server.id, log.message))
		if message.strip()[1:-1] in log.message:
			return True
	raise AssertionError("Not see message %s in scripts logs" % message)


# @step('I reboot scalarizr$')
# def reboot_scalarizr(step):
# 	c = Cloud()
#
# 	world.node = c.get_node(world.server)
# 	world.node.run('/etc/init.d/scalarizr restart')
# 	LOG.info('Scalarizr restart complete')

#
# @step("see 'Scalarizr terminated' in log")
# def check_log(step):
# 	#TODO: More smart alghoritm
# 	time.sleep(15)
# 	LOG.info('Check scalarizr log for  termination')
# 	out = world.node.run('cat /var/log/scalarizr_debug.log | grep "Scalarizr terminated"')[0]
# 	world.assert_not_in('Scalarizr terminated', out, 'Scalarizr was not restarting')
#
#
# @step('scalarizr process is ([\d]+)$')
# def check_processes(step, count):
# 	time.sleep(60)
# 	list_proc = world.node.run('ps aux | grep scalarizr')[0]
# 	c = 0
# 	for pr in list_proc.split('\n'):
# 		if 'bin/scalarizr' in pr:
# 			c += 1
# 	LOG.info('Scalarizr count of processes %s' % c)
# 	world.assert_not_equal(c, int(count), 'Scalarizr processes is: %s but processes \n%s' % (c, list_proc))
#
#
# @step('not ERROR in log')
# def check_error_in_log(step):
# 	out = world.node.run('cat /var/log/scalarizr_debug.log | grep ERROR')[0]
# 	LOG.info('Check scalarizr error')
# 	errors = []
# 	if 'ERROR' in out:
# 		log = out.splitlines()
# 		for l in log:
# 			try:
# 				d = datetime.strptime(l.split()[0], '%Y-%m-%d')
# 			except:
# 				continue
# 			now = datetime.now()
# 			if not d.year == now.year or not d.month == now.month or not d.day == now.day:
# 				continue
# 			errors.append(l)
# 	if errors:
# 		raise AssertionError('ERROR in log: %s' % errors)


@step("I deploy app with name '(.+)'")
def deploy_app(step, app_name):
	LOG.info('Deploy app %s' % app_name)
	old_tasks_ids = [task['id'] for task in IMPL.deploy.tasks_list()]
	LOG.debug('Old tasks %s' % old_tasks_ids)
	world.farm.deploy_app(app_name, path='/tmp')
	time.sleep(10)
	new_tasks_ids = [task['id'] for task in IMPL.deploy.tasks_list()]
	LOG.debug('New tasks %s' % new_tasks_ids)
	task_id = [task for task in new_tasks_ids if not task in old_tasks_ids]
	world.task_id = task_id[0]
	LOG.info('Task id is %s' % world.task_id)


@step('And deploy task deployed')
def check_deploy_status(step):
	time.sleep(5)
	LOG.info('Check task status')
	LOG.debug('All tasks %s' % IMPL.deploy.tasks_list())
	task = filter(lambda x: x['id'] == world.task_id, IMPL.deploy.tasks_list())[0]
	world.assert_not_equal(task['status'], 'deployed', 'Task not deployed, status: %s' % task['status'])


@step('I define event \'(.+)\'$')
def define_event_to_role(step, event):
	events = IMPL.event.list()
	res = filter(lambda x: x['name'] == event, events)
	if not res:
		LOG.info('Create new Event')
		IMPL.event.change(event, 'Revizor FireEvent')
	res = filter(lambda x: x['name'] == event, events)[0]
	setattr(world, 'last_event', res)


@step('I attach a script \'(.+)\' on this event')
def attach_script(step, script_name):
	scripts = IMPL.script.list()
	res = filter(lambda x: x['name'] == script_name, scripts)[0]
	LOG.info('Add script %s to custom event %s' % (res['name'], world.last_event['name']))
	IMPL.farm.edit_role(world.farm.id, world.role.role.id, scripting=[{
		              "script_id": str(res['id']),
		              "script": res['name'],
		              "params": [],
		              "target": "instance",
		              "version": "1",
		              "timeout": "1200",
		              "issync": "1",
		              "order_index": "1",
		              "event": world.last_event['name']
	                }]
				)


@step('I execute \'(.+)\' in (.+)$')
def execute_command(step, command, serv_as):
	c = Cloud()
	node = c.get_node(getattr(world, serv_as))
	LOG.info('Execute command on server: %s' % command)
	node.run(command)


@step('server ([\w\d]+) contain \'(.+)\'')
def check_file(step, serv_as, path):
	c = Cloud()
	node = c.get_node(getattr(world, serv_as))
	out = node.run('ls %s' % path)
	LOG.info('Check exist path: %s' % path)
	if not out[2] == 0:
		raise AssertionError('File \'%s\' not exist: %s' % (path, out))


def check_script_log(*args, **kwargs):
	world.server.scriptlogs.reload()
	if len(world.server.scriptlogs) > world.server_script_count:
		world.scriptlog = world.server.scriptlogs
		return True
	return False
