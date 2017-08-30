import re
import time
import logging

import chef

from lettuce import world, step


LOG = logging.getLogger(__name__)


@step("script ([\w\d -/\:/\.]+) executed in ([\w\d]+) by user (\w+) with exitcode (\d+)(?: and contain ([\w\d \.!:;=>\"/]+)?)? for ([\w\d]+)")
def assert_check_script_in_log(step, name, event, user, exitcode, contain, serv_as):
    world.check_script_executed(serv_as=serv_as,
                                name=name,
                                event=event,
                                user=user,
                                log_contains=contain,
                                exitcode=exitcode)


@step("script output contains '(.+)' in (.+)$")
def assert_check_message_in_log(step, message, serv_as):
    server = getattr(world, serv_as)
    script_name = getattr(world, '_server_%s_last_script_name' % server.id)
    world.check_script_executed(serv_as=serv_as,
                                name=script_name,
                                log_contains=message,
                                new_only=True)


@step(r"script result contains '([\w\W]+)?' on ([\w\d]+)")
def assert_check_message_in_log_table_view(step, script_output, serv_as):
    if script_output:
        for line in script_output.split(';'):
            external_step = "script output contains '{result}' in {server}".format(
                result=line.strip(),
                server=serv_as)
            LOG.debug('Run external step: %s' % external_step)
            step.when(external_step)


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
    failure_markers = [
        'Command "/usr/bin/chef-client" exited with code 1',
        'Command /usr/bin/chef-client exited with code 1']
    for m in failure_markers:
        out = node.run('grep %s /var/log/scalarizr_debug.log' % m)[0]
        if out.strip():
            return
    raise AssertionError("Chef bootstrap markers not found in scalarizr_debug.log")


@step("I check that text '([\w\W]+)?' is in the STDERR section of script logs in ([\w\d]+)")
def check_for_error_text(step, err_text, serv_as):
    server = getattr(world, serv_as)
    server.sciptlogs.reload()
    stderr_msg = server.scriptlogs[0].message
    stderr_msg = stderr_msg[:stderr_msg.find('STDOUT')]
    if err_text not in stderr_msg:
        raise AssertionError('STDERR message "%s" not exist in script logs!' % stderr_msg)
