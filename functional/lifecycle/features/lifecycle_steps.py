import os
import time
import json
import logging

from lettuce import world, step

from revizor2.api import Farm, IMPL
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.consts import ServerStatus, Platform

LOG = logging.getLogger('lifecycle')


@step('I see (.+) server (.+)$')
def waiting_for_assertion(step, spec, serv_as, timeout=1400):
    if CONF.main.platform == 'ucloud':
        timeout = 2000
    #server = wait_until(world.check_server_status, args=(spec, world.role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    server = world.wait_server_bootstrapping(world.role, spec)
    setattr(world, serv_as, server)
    LOG.info('Server succesfully %s' % spec)


@step('I wait and see (.+) server (.+)$')
def waiting_server(step, spec, serv_as, timeout=1400):
    if CONF.main.dist.startswith('win'):
        timeout = 2400
    #server = wait_until(world.check_server_status, args=(spec, world.role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    server = world.wait_server_bootstrapping(world.role, spec)
    LOG.info('Server succesfully %s' % spec)
    setattr(world, serv_as, server)


@step('I have (.+) server (.+)$')
def having_server(step, state, serv_as):
    server = getattr(world, serv_as)
    world.assert_not_equal(server.status, ServerStatus.from_code(state), "Server %s is not in state %s" % (server.id, state))


#TODO: Add check hostup message and direction
@step("I save (\w+) configuration in '([\w]+)' message in ([\w\d]+)$")
def save_config_from_message(step, config_group, message, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Get messages from server %s' % server.id)
    messages = world.get_szr_messages(node)
    msg_id = filter(lambda x: x['name'] == message, messages)[0]['id']
    LOG.info('Message id for %s is %s' % (message, msg_id))
    message_details = json.loads(node.run('szradm message-details %s --json' % msg_id)[0])['body']
    LOG.info('Message details is %s' % message_details)
    LOG.info('Save message part %s' % config_group)
    setattr(world, '%s_%s_%s' % (serv_as, message.lower(), config_group), message_details[config_group])


@step("(\w+) configuration in '([\w]+)' message in ([\w\d]+) is old")
def check_message_config(step, config_group, message, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Get messages from server %s' % server.id)
    messages = world.get_szr_messages(node)
    msg_id = filter(lambda x: x['name'] == message, messages)[0]['id']
    LOG.info('Message id for %s is %s' % (message, msg_id))
    message_details = json.loads(node.run('szradm message-details %s --json' % msg_id)[0])['body']
    LOG.info('Message details is %s' % message_details)
    old_details = getattr(world, '%s_%s_%s' % (serv_as, message.lower(), config_group), '')
    if not config_group in message_details or old_details == message_details[config_group]:
        LOG.error('New and old details is not equal: %s\n %s' % (old_details, message_details[config_group]))
        raise AssertionError('New and old details is not equal')


@step("[directory|file] '(.+)' exist in (.+)$")
def check_path(step, path, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    out = node.run('/bin/ls %s' % path)
    LOG.info('Check directory %s' % path)
    if 'No such file or directory' in out[0] or 'No such file or directory' in out[1]:
        LOG.error('Directory (file) not exist')
        raise AssertionError("'%s' not exist in server %s" % (path, server.id))


@step("I create (\d+) files in '(.+)' in ([\w\d]+)")
def create_files(step, file_count, directory, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Create %s files in directory %s' % (file_count, directory))
    node.run('cd %s && for (( i=0;i<%s;i++ )) do touch "file$i"; done' % (directory, file_count))


@step("count of files in directory '(.+)' is (\d+) in ([\w\d]+)")
def check_file_count(step, directory, file_count, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Check count of files in directory %s' % directory)
    out = node.run('cd %s && ls' % directory)[0].split()
    for i in ['..', '.', '...', 'lost+found']:
        try:
            out.remove(i)
        except ValueError:
            continue
    if not int(file_count) == len(out):
        raise AssertionError('Count of files in directory is not %s, is %s' % (file_count, out))


@step('I see execution result in scripting log')
def check_result_script_log(step):
    wait_until(check_script_log, timeout=1000, error_text="I'm not see messages in script logs")


@step("script output contains '(.+)' in (.+)$")
def assert_check_message_in_log(step, message, serv_as):
    #TODO: Rewrite this, because 2 identically script not work
    time.sleep(60)
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        LOG.debug('Server %s log content: %s' % (server.id, log.message))
        if message.strip()[1:-1] in log.message:
            return True
    raise AssertionError("Not see message %s in scripts logs" % message)


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
    time.sleep(30)
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
    node = world.cloud.get_node(getattr(world, serv_as))
    LOG.info('Execute command on server: %s' % command)
    node.run(command)


@step('server ([\w\d]+) contain \'(.+)\'')
def check_file(step, serv_as, path):
    node = world.cloud.get_node(getattr(world, serv_as))
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
