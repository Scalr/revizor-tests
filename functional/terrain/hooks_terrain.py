__author__ = 'gigimon'
import os
import logging
from datetime import datetime

from lettuce import world, after, before

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.cloud import Cloud
from revizor2.cloud.node import ExtendedNode
from revizor2.consts import ServerStatus


LOG = logging.getLogger(__name__)


@before.all
def initialize_world():
    setattr(world, 'test_start_time', datetime.now())
    c = Cloud()
    setattr(world, 'cloud', c)


@after.each_scenario
def get_all_logs(scenario):
    """Give scalarizr_debug.log logs from servers"""
    #Get path
    if CONF.main.dist.startswith('win'):
        return
    LOG.warning('Get scalarizr logs after scenario %s' % scenario.name)
    farm = getattr(world, 'farm', None)
    if not farm:
        LOG.error("Farm does not exists. Can't get logs. Exit from step.")
        return
    farm.servers.reload()
    servers = farm.servers
    test_name = scenario.described_at.file.split('/')[-1].split('.')[0]
    LOG.debug('Test name: %s' % test_name)
    start_time = world.test_start_time
    path = os.path.realpath(os.path.join(CONF.main.logpath, 'scalarizr', test_name,
                                         start_time.strftime('%m%d-%H:%M'), scenario.name.replace('/', '-')))
    LOG.debug('Path to save log: %s' % path)
    if not os.path.exists(path):
        os.makedirs(path, 0755)

    for server in servers:
        if server.status == ServerStatus.RUNNING or \
                        server.status == ServerStatus.INIT or \
                        server.status == ServerStatus.PENDING:
            try:
                #Get log from remote host
                server.get_logs('scalarizr_debug.log', os.path.join(path, server.id + '_scalarizr_debug.log'))
                LOG.info('Save scalarizr log from server %s to %s' \
                         % (server.id, os.path.join(path, server.id + '_scalarizr_debug.log')))
                LOG.info('Compressing /etc/scalr directory')
                #Get configs and role behavior from remote host
                server.get_configs(os.path.join(path, server.id + '_scalr_configs.tar.gz'), compress=True)
                LOG.info('Download archive with scalr directory and behavior to: %s' \
                         % os.path.join(path, server.id + '_scalr_configs.tar.gz'))
            except BaseException, e:
                LOG.error('Error in downloading configs: %s' % e)
                continue


@after.all
def cleanup_all(total):
    """If not have problem - stop farm and delete roles, vhosts, domains"""
    LOG.info('Failed steps: %s' % total.steps_failed)
    LOG.debug('Results %s' % total.scenario_results)
    LOG.debug('Passed %s' % total.scenarios_passed)
    if not total.steps_failed and CONF.main.stop_farm:
        LOG.info('Clear and stop farm...')
        farm = getattr(world, 'farm', None)
        if not farm:
            return
        role = getattr(world, world.role_type + '_role', None)
        if not role:
            IMPL.farm.clear_roles(world.farm.id)
            return
        IMPL.farm.clear_roles(world.farm.id)
        new_role_id = getattr(world, 'new_role_id', None)
        if new_role_id:
            LOG.info('Delete bundled role: %s' % new_role_id)
            try:
                IMPL.role.delete(new_role_id, delete_image=True)
            except:
                pass
        cloud_node = getattr(world, 'cloud_server', None)
        if cloud_node:
            LOG.info('Destroy node in cloud')
            try:
                cloud_node.destroy()
            except BaseException, e:
                LOG.error('Node %s can\'t be destroyed: %s' % (cloud_node.id, e))
        world.farm.terminate()
        world.farm.vhosts.reload()
        world.farm.domains.reload()
        for vhost in world.farm.vhosts:
            LOG.info('Delete vhost: %s' % vhost.name)
            vhost.delete()
        for domain in world.farm.domains:
            LOG.info('Delete domain: %s' % domain.name)
            domain.delete()
    else:
        farm = getattr(world, 'farm', None)
        if not farm:
            return
        world.farm.roles.reload()
        for r in world.farm.roles:
            IMPL.farm.edit_role(world.farm.id, r.role_id, options={"system.timeouts.reboot": 999999,
                                                                   "system.timeouts.launch": 999999})
    for v in dir(world):
        if isinstance(getattr(world, v), ExtendedNode):
            world.__delattr__(v)