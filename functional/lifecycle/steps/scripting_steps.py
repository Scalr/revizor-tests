import re
import time
import logging

import chef

from lettuce import world, step
from revizor2.conf import CONF


LOG = logging.getLogger(__name__)


@step("script ([\w\d -/\:/\.]+) executed in ([\w\d]+)(?: by user (\w+)?)? with exitcode (\d+)(?: and contain ([\w\d \.!:;=>\"/]+)?)? for ([\w\d]+)")
def assert_check_script_in_log(step, name, event, user, exitcode, contain, serv_as):
    std_err = False
    if contain and contain.startswith('STDERR:'):
        contain = re.sub(r'STDERR: ', '', contain).strip()
        std_err = True
    world.check_script_executed(serv_as=serv_as,
                                name=name,
                                event=event,
                                user=user,
                                log_contains=contain,
                                std_err=std_err,
                                exitcode=exitcode)


@step("script( stderr)? output contains '(.*)' in (.+)$")
def assert_check_message_in_log(step, stream, message, serv_as):
    server = getattr(world, serv_as)
    script_name = getattr(world, '_server_%s_last_script_name' % server.id)
    world.check_script_executed(serv_as=serv_as,
                                name=script_name,
                                log_contains=message,
                                std_err=bool(stream),
                                new_only=True)


@step("([\w\d]+) chef runlist has only recipes \[([\w\d,.]+)\]")
def verify_recipes_in_runlist(step, serv_as, recipes):
    recipes = recipes.split(',')
    server = getattr(world, serv_as)

    host_name = world.get_hostname_by_server_format(server)
    chef_api = chef.autoconfigure()

    run_list = chef.Node(host_name, api=chef_api).run_list
    if len(run_list) != len(recipes):
        raise AssertionError('Count of recipes in node is another that must be: "%s" != "%s" "%s"' %
                             (len(run_list), len(recipes), run_list))
    if not all(recipe in ','.join(run_list) for recipe in recipes):
        raise AssertionError('Recipe "%s" not exist in run list!' % run_list)


@step("chef bootstrap failed in ([\w\d]+)")
def chef_bootstrap_failed(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    if CONF.feature.dist.is_windows:
        win_failure_marker = 'chef-client" exited with code 1'
        cmd = 'findstr /C:"Command \\"C:\opscode\chef\\bin\chef-client\\" exited with code 1"' \
              ' "C:\opt\scalarizr\\var\log\scalarizr_debug.log"'
        result = node.run(cmd)
        LOG.debug('Logs from server:\n%s\n%s\n%s' % (result.std_out, result.std_err, result.status_code))
        if win_failure_marker in result.std_out:
            return
    else:
        failure_markers = [
            'Command "/usr/bin/chef-client" exited with code 1',
            'Command /usr/bin/chef-client exited with code 1']
        for m in failure_markers:
            out = node.run('grep %s /var/log/scalarizr_debug.log' % m).std_out
            if out.strip():
                return
    raise AssertionError("Chef bootstrap marker not found in scalarizr_debug.log out: %s" % out)


@step("last script data is deleted on ([\w\d]+)$")
def check_script_data_deleted(step, serv_as):
    LOG.info('Check script executed data was deleted')
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    if not server.scriptlogs:
        raise AssertionError("No orchestration logs found on %s" % server.id)
    task_dir = server.scriptlogs[0].execution_id.replace('-', '')
    node = world.cloud.get_node(server)
    if CONF.feature.dist.is_windows:
        cmd = 'dir c:\\opt\\scalarizr\\var\\lib\\tasks\\%s /b /s /ad | findstr /e "\\bin \\data"' % task_dir
        for _ in range(3):
            out = node.run(cmd)
            if out.status_code:
                time.sleep(10)
                continue
        LOG.debug('Logs from server:\n%s\n%s\n%s' % (out.std_out, out.std_err, out.status_code))
    else:
        cmd = 'find /var/lib/scalarizr/tasks/%s -type d -regex ".*/\\(bin\\|data\\)"' % task_dir
        out = node.run(cmd)
        LOG.debug('Logs from server:\n%s\n%s\n%s' % (out.std_out, out.std_err, out.status_code))
        if out.status_code:
            raise AssertionError("Command '%s' was not executed properly. An error has occurred:\n%s" % (cmd, out.std_err))
        folders = [line for line in out.std_out.splitlines() if line.strip()]
        if folders:
            raise AssertionError("Script data is not deleted on %s. Found folders: %s" % (server.id, ';'.join(folders)))
