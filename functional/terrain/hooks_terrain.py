__author__ = 'gigimon'
import os
import re
import logging
from datetime import datetime

from lettuce import world, after, before

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.cloud import Cloud
from revizor2.cloud.node import ExtendedNode
from revizor2.consts import ServerStatus, Dist
from revizor2.fixtures import manifests

LOG = logging.getLogger(__name__)


@before.all
def initialize_world():
    setattr(world, 'test_start_time', datetime.now())
    c = Cloud()
    setattr(world, 'cloud', c)


@before.each_feature
def exclude_scenarios_by_version(feature):
    """
    This hook remove some scenarios in depends from role version.
    You can set in .manifest file EXCLUDE_SCENARIOS variable with version software
    and scenarios which You want exclude from test in this role version.

    >>> EXCLUDE_SCENARIOS= {
    >>>    "default": ["Bootstrapping role"],
    >>>    "26": ["Bundling data", "Modifying data"]
    >>> }
    """
    #TODO: Implement version operator > < => =<
    version = 'default'
    if CONF.feature.role_id:
        role = IMPL.role.get(CONF.feature.role_id)
        version = re.findall('(\d+)', role['name'].split('-')[0])
        version = int(version[0]) if version else 'default'

    manifest = os.path.realpath(
        os.path.join(os.path.dirname(feature.scenarios[0].with_file.split('.')[0]),
                     'manifests',
                     feature.described_at.file.split('.')[0].split('/')[-1] + '.manifest')
    )
    if not os.path.isfile(manifest):
        LOG.warning("Manifest file %s doesn't exist")
        return
    manifest = manifests(manifest)
    if 'EXCLUDED_SCENARIOS' in manifest:
        excluded_scenarios_name = manifest['EXCLUDED_SCENARIOS'].get(version, [])
        LOG.info('Exclude the following scenarios %s from test because role version: %s' %
                 (excluded_scenarios_name, version))
        new_scenarios_list = []
        for scenario in feature.scenarios:
            if not scenario.name in excluded_scenarios_name:
                new_scenarios_list.append(scenario)
        if new_scenarios_list:
            feature.scenarios = new_scenarios_list


@before.each_scenario
def exclude_steps_by_options(scenario):
    """
    Exclude steps from feature for @world.run_only_if
    """
    steps_to_remove = []
    for step in scenario.steps:
        func = step._get_match(None)[1].function
        if hasattr(func, '_exclude'):
            steps_to_remove.append(step)
    for step in steps_to_remove:
        scenario.steps.remove(step)


@after.each_scenario
def get_all_logs(scenario):
    """Give scalarizr_debug.log logs from servers"""
    # Get Farm
    LOG.warning('Get scalarizr logs after scenario %s' % scenario.name)
    farm = getattr(world, 'farm', None)
    if not farm:
        LOG.error("Farm does not exists. Can't get logs. Exit from step.")
        return
    farm.servers.reload()
    # Get servers
    servers = farm.servers
    # Get test
    test_name = scenario.described_at.file.split('/')[-1].split('.')[0]
    LOG.debug('Test name: %s' % test_name)
    # Get path
    start_time = world.test_start_time
    path = os.path.realpath(os.path.join(CONF.main.log_path, 'scalarizr',
                                         test_name,
                                         start_time.strftime('%m%d-%H:%M'),
                                         scenario.name.replace('/', '-')))
    LOG.debug('Path to save log: %s' % path)
    if not os.path.exists(path):
        os.makedirs(path, 0755)
    # Get logs && configs
    for server in servers:
        logs = [
            # debug log
            {'file': os.path.join(path, '_'.join((server.id, 'scalarizr_debug.log'))),
             'log_type': 'debug',
             'compress': True},
            # update log
            {'file': os.path.join(path, '_'.join((server.id, 'scalarizr_update.log'))),
             'log_type': 'update',
             'compress': True}]
        if server.status == ServerStatus.RUNNING or \
            server.status == ServerStatus.INIT or \
            server.status == ServerStatus.PENDING:
            try:
                #Get log from remote host
                for log in logs:
                    server.get_log_by_api(**log)
                    LOG.info('Save {log_type} log from server {} to {file}'.format(server.id, **log))
                    #Get configs and role behavior from remote host only for linux family
                    if not Dist.is_windows_family(server.role.dist):
                        file = os.path.join(path, '_'.join((server.id, 'scalr_configs.tar.gz')))
                        server.get_configs(file, compress=True)
                        LOG.info('Download archive with scalr directory and behavior to: {}'.format(file))
            except BaseException, e:
                LOG.error('Error in downloading configs: %s' % e)
                continue


@after.all
def cleanup_all(total):
    """If not have problem - stop farm and delete roles, vhosts, domains"""
    LOG.info('Failed steps: %s' % total.steps_failed)
    LOG.debug('Results %s' % total.scenario_results)
    LOG.debug('Passed %s' % total.scenarios_passed)
    if not total.steps_failed and CONF.feature.stop_farm:
        LOG.info('Clear and stop farm...')
        farm = getattr(world, 'farm', None)
        if not farm:
            return
        IMPL.farm.clear_roles(world.farm.id)
        bundled_role_id = getattr(world, 'bundled_role_id', None)
        if bundled_role_id:
            LOG.info('Delete bundled role: %s' % bundled_role_id)
            try:
                IMPL.role.delete(bundled_role_id, delete_image=True)
            except BaseException, e:
                LOG.exception('Error on deletion role %s' % bundled_role_id)
        cloud_node = getattr(world, 'cloud_server', None)
        if cloud_node:
            LOG.info('Destroy node in cloud')
            try:
                cloud_node.destroy()
            except BaseException, e:
                LOG.exception('Node %s can\'t be destroyed' % cloud_node.id)
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