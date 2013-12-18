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


@step("([\w]+) event in script log for ([\w\d]+) from user (\w+) and exitcode (\d+)")
def assert_check_script_in_log(step, message, serv_as, user, exitcode):
    time.sleep(5)
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        LOG.debug('Check script log: %s/%s/%s' % (log.message, log.run_as, log.exitcode))
        if log.event.strip() == message.strip() and log.run_as == user:
            LOG.debug('We found event \'%s\' run from user %s' % (log.event, log.run_as))
            if log.exitcode == int(exitcode):
                LOG.debug('This message exitcode: %s' % log.exitcode)
                return True
            else:
                raise AssertionError('Script on event \'%s\' (%s) exit with code: %s but lookup: %s'
                                     % (message, user, log.exitcode, exitcode))
    raise AssertionError('I\'m not see script on event \'%s\' (%s) in script logs for server %s' % (message, user, server.id))


@step('I see script result in (.+)')
def assert_check_script_work(step, serv_as):
    time.sleep(30)
    serv = getattr(world, serv_as)
    serv.scriptlogs.reload()
    last_count = getattr(world, '%s_script_count' % serv_as)
    if not len(serv.scriptlogs) == last_count+1:
        LOG.warning('Last count of script logs: %s, new: %s, must be: %s' % (last_count, len(serv.scriptlogs), last_count+1))
        raise AssertionError('Not see script result in script logs')
