__author__ = 'gigimon'
import logging

from lettuce import world, step

from revizor2.api import Script
from revizor2.utils import wait_until
from revizor2.consts import ServerStatus


LOG = logging.getLogger(__name__)


@step('I expect server bootstrapping as ([\w\d]+)(?: in (.+) role)?$')
def expect_server_bootstraping_for_role(step, serv_as, role_type, timeout=2000):
    """Expect server bootstrapping to 'Running' and check every 10 seconds scalarizr log for ERRORs and Traceback"""
    role = world.get_role(role_type)
    LOG.info('Expect server bootstrapping as %s for %s role' % (serv_as, role_type))
    server = world.wait_server_bootstrapping(role, ServerStatus.RUNNING, timeout=timeout)
    setattr(world, serv_as, server)


@step(r'I terminate server ([\w]+)$')
def terminate_server(step, serv_as):
    """Terminate server (no force)"""
    server = getattr(world, serv_as)
    LOG.info('Terminate server %s' % server.id)
    server.terminate()


@step(r'I terminate server ([\w]+) with decrease')
def terminate_server_decrease(step, serv):
    """Terminate server (no force), but with decrease"""
    server = getattr(world, serv)
    LOG.info('Terminate server %s with decrease' % server.id)
    server.terminate(decrease=True)


@step('I force terminate ([\w\d]+)$')
def terminate_server_force(step, serv_as):
    """Terminate server force"""
    server = getattr(world, serv_as)
    LOG.info('Terminate server %s force' % server.id)
    server.terminate(force=True)


@step('I force terminate server ([\w\d]+) with decrease$')
def terminate_server_force(step, serv_as):
    """Terminate server force"""
    server = getattr(world, serv_as)
    LOG.info('Terminate server %s force' % server.id)
    server.terminate(force=True, decrease=True)


@step('I reboot server (.+)$')
def reboot_server(step, serv_as):
    server = getattr(world, serv_as)
    server.reboot()
    LOG.info('Server %s was rebooted' % serv_as)


@step('Scalr ([^ .]+) ([^ .]+) (?:to|from) ([^ .]+)')
def assert_get_message(step, msgtype, msg, serv_as, timeout=1500):
    """Check scalr in/out message delivering"""
    LOG.info('Check message %s %s server %s' % (msg, msgtype, serv_as))
    if serv_as == 'all':
        world.farm.servers.reload()
        server = [serv for serv in world.farm.servers if serv.status == ServerStatus.RUNNING]
        world.wait_server_message(server, msg.strip(), msgtype, find_in_all=True, timeout=timeout)
    else:
        try:
            LOG.info('Try get server %s in world' % serv_as)
            server = getattr(world, serv_as)
        except AttributeError, e:
            LOG.debug('Error in server found message: %s' % e)
            world.farm.servers.reload()
            server = [serv for serv in world.farm.servers if serv.status == ServerStatus.RUNNING]
        LOG.info('Wait message %s / %s in servers: %s' % (msgtype, msg.strip(), server))
        s = world.wait_server_message(server, msg.strip(), msgtype, timeout=timeout)
        setattr(world, serv_as, s)


@step("I execute script '(.+)' (.+) on (.+)")
def execute_script(step, script_name, exec_type, serv_as):
    synchronous = 1 if exec_type.strip() == 'synchronous' else 0
    serv = getattr(world, serv_as)
    script = Script.get_id(script_name)
    LOG.info('Execute script id: %s, name: %s' % (script['id'], script_name))
    serv.scriptlogs.reload()
    setattr(world, '%s_script_count' % serv_as, len(serv.scriptlogs))
    LOG.debug('Count of complete scriptlogs: %s' % len(serv.scriptlogs))
    Script.script_execute(world.farm.id, serv.farm_role_id, serv.id, script['id'], synchronous, script['version'])
    LOG.info('Script execute success')


@step('wait all servers are terminated')
def wait_all_terminated(step):
    """Wait termination of all servers"""
    wait_until(world.wait_farm_terminated, timeout=1800, error_text='Servers in farm not terminated too long')


