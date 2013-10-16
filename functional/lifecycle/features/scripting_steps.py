import time
import logging

from lettuce import world, step

from revizor2.utils import wait_until


LOG = logging.getLogger('scripting')


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
    time.sleep(60)
    serv = getattr(world, serv_as)
    serv.scriptlogs.reload()
    last_count = getattr(world, '%s_script_count' % serv_as)
    if not len(serv.scriptlogs) == last_count+1:
        LOG.warning('Last count of script logs: %s, new: %s' % (last_count, len(serv.scriptlogs)))
        raise AssertionError('Not see script result in script logs')
