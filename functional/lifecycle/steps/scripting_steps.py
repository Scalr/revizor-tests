import time
import logging
import re

from lettuce import world, step

from revizor2.utils import wait_until


LOG = logging.getLogger('scripting')


@step("([\w]+) script executed scalarizr is in '(.+)' state in (.+)")
def assert_check_script(step, message, state, serv_as):
    serv = getattr(world, serv_as)
    wait_until(world.wait_script_execute, args=(serv, message, state), timeout=600,
               error_text='I\'m not see %s scripts execution for server %s' % (message, serv.id))


@step("script ([\w\d -/]+) executed in ([\w\d]+) by user (\w+) with exitcode (\d+) and contain ([\w\d !:]+)? for ([\w\d]+)")
def assert_check_script_in_log(step, name, event, user, exitcode, contain, serv_as):
    LOG.debug('Check script in log by parameters: \nname: %s\nevent: %s\user: %s\nexitcode: %s\ncontain: %s' %
              (name, event, user, exitcode, contain)
    )
    time.sleep(5)
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    # Convert script name, because scalr convert name to:
    # substr(preg_replace("/[^A-Za-z0-9]+/", "_", $script->name), 0, 50)
    name = re.sub('[^A-Za-z0-9/.]+', '_', name)[:50] if name else name
    for log in server.scriptlogs:
        LOG.debug('Check script log:\nname: %s\nevent: %s\nmessage: %s\nrun as: %s\nexitcode: %s\n' %
                  (log.name, log.event, log.message, log.run_as, log.exitcode))

        if log.event.strip() == event.strip() \
                and log.run_as == user \
                and ((name == 'chef' and log.name.strip().startswith(name))
                     or (name == 'local' and log.name.strip().startswith(name))
                     or log.name.strip() == name):

            LOG.debug('We found event \'%s\' run from user %s' % (log.event, log.run_as))
            if log.exitcode == int(exitcode):
                LOG.debug('Log message output: %s' % log.message)
                if contain and (not contain in log.message):
                    raise AssertionError('Script on event \'%s\' (%s) contain: %s but lookup: %s'
                                         % (event, user, log.message, contain))
                LOG.debug('This event exitcode: %s' % log.exitcode)
                return True
            else:
                raise AssertionError('Script on event \'%s\' (%s) exit with code: %s but lookup: %s'
                                     % (event, user, log.exitcode, exitcode))
    raise AssertionError('I\'m not see script on event \'%s\' (%s) in script logs for server %s' % (event, user, server.id))


@step('I see script result in (.+)')
def assert_check_script_work(step, serv_as):
    server = getattr(world, serv_as)
    last_count = len(getattr(world, '_server_%s_last_scripts' % server.id))
    server.scriptlogs.reload()
    for i in range(6):
        if not len(server.scriptlogs) == last_count+1:
            LOG.warning('Last count of script logs: %s, new: %s, must be: %s' % (last_count, len(server.scriptlogs), last_count+1))
            time.sleep(15)
            server.scriptlogs.reload()
            continue
        break
    else:
        raise AssertionError('Not see script result in script logs')


@step("script output contains '(.+)' in (.+)$")
def assert_check_message_in_log(step, message, serv_as):
    server = getattr(world, serv_as)
    last_scripts = getattr(world, '_server_%s_last_scripts' % server.id)
    server.scriptlogs.reload()
    for log in server.scriptlogs:
        if log in last_scripts:
            continue
        LOG.debug('Server %s log content: %s' % (server.id, log.message))
        if message.strip()[1:-1] in log.message:
            return True
    raise AssertionError("Not see message %s in scripts logs" % message)