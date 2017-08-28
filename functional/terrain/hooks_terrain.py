import os
import re
import sys
import uuid
import json
import semver
import logging
from base64 import b64decode
from datetime import datetime
from operator import itemgetter
from distutils.version import LooseVersion

import github
import requests
from lxml import etree
from lettuce import world, after, before

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.cloud.node import ExtendedNode
from revizor2.consts import ServerStatus, Dist
from revizor2.fixtures import manifests
from revizor2.defaults import DEFAULT_SCALARIZR_DEVEL_REPOS, DEFAULT_SCALARIZR_RELEASE_REPOS
from revizor2.helpers.parsers import parser_for_os_family


LOG = logging.getLogger(__name__)

OUTLINE_ITERATOR = {}
PKG_UPDATE_SUITES = ['Linux update for new package test', 'Windows update for new package test']

ORG = 'Scalr'
GH = github.GitHub(access_token=CONF.credentials.github.access_token)


def get_all_logs_and_info(scenario, outline='', outline_failed=None):
    if CONF.feature.platform.is_azure:
        return
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
                                         scenario.name.replace('/', '-'),
                                         outline))
    LOG.debug('Path to save log: %s' % path)
    if not os.path.exists(path):
        os.makedirs(path, 0o755)
    # Get logs && configs
    for server in servers:
        if not server.is_scalarized: continue
        logs = [
            # debug log
            {'file': os.path.join(path, '_'.join((server.id, 'scalarizr_debug.log'))),
             'log_type': 'debug',
             'compress': True},
            # update log
            {'file': os.path.join(path, '_'.join((server.id, 'scalarizr_update.log'))),
             'log_type': 'update',
             'compress': True}]
        if server.status in [ServerStatus.PENDING, ServerStatus.INIT, ServerStatus.RUNNING]:
            try:
                #Get log from remote host
                for log in logs:
                    server.get_log_by_api(**log)
                    LOG.info('Save {log_type} log from server {} to {file}'.format(server.id, **log))
                    #Get configs and role behavior from remote host only for linux family
                    if not Dist(server.role.dist).is_windows:
                        file = os.path.join(path, '_'.join((server.id, 'scalr_configs.tar.gz')))
                        server.get_configs(file, compress=True)
                        LOG.info('Download archive with scalr directory and behavior to: {}'.format(file))
            except BaseException as e:
                LOG.error('Error in downloading configs: %s' % e)
                continue
        if server.status == ServerStatus.RUNNING and not CONF.feature.dist.is_windows:
            node = world.cloud.get_node(server)
            out = node.run("ps aux | grep 'bin/scal'")[0]
            for line in out.splitlines():
                ram = line.split()[5]
                if len(ram) > 3:
                    ram = '%sMB' % ram[:-3]
                if 'bin/scalr-upd-client' in line:
                    LOG.info('Server %s use %s RAM for update-client' % (server.id, ram))
                    world.wrt(etree.Element('meta', name='szrupdateram', value=ram, serverid=server.id))
                elif 'bin/scalarizr' in line:
                    LOG.info('Server %s use %s RAM for scalarizr' % (server.id, ram))
                    world.wrt(etree.Element('meta', name='szrram', value=ram, serverid=server.id))
    # Save farm, domains and messages info if scenario has failed
    if scenario.failed or outline_failed:
        domains = None
        try:
            domains = IMPL.domain.list(farm_id=farm.id)
        except Exception as e:
            if not 'You do not have permission to view this component' in str(e):
                raise
        LOG.warning("Get farm settings after test failure")
        farm_settings = IMPL.farm.get_settings(farm_id=farm.id)
        if servers:
            LOG.warning("Get scalarizr messages for every server after test failure")
            try:
                for server in servers:
                    server.messages.reload()
                    server_messages = []
                    for msg in server.messages:
                        server_messages.append({msg.name: {'message': msg.message,
                            'date': str(msg.date),
                            'delivered': msg.delivered,
                            'status': msg.status,
                            'type': msg.type,
                            'id': msg.id}})
                    # Save server messages
                    with open(os.path.join(path, '%s_messages.json' % server.id), "w+") as f:
                        f.write(json.dumps(server_messages, indent=2))
            except:
                pass
        # Save farm settings
        with open(os.path.join(path, 'farm_settings.json'), "w+") as f:
            f.write(json.dumps(farm_settings, indent=2))
        # Save domains list
        if domains:
            with open(os.path.join(path, 'domains.json'), "w+") as f:
                f.write(json.dumps(domains, indent=2))


def get_scalaraizr_latest_version(branch):
    os_family = CONF.feature.dist.family
    if branch in ['stable', 'latest']:
        default_repo = DEFAULT_SCALARIZR_RELEASE_REPOS[os_family]
    else:
        url = DEFAULT_SCALARIZR_DEVEL_REPOS['url'][CONF.feature.ci_repo]
        path = DEFAULT_SCALARIZR_DEVEL_REPOS['path'][os_family]
        default_repo = url.format(path=path)
    index_url = default_repo.format(branch=branch)
    repo_data = parser_for_os_family(CONF.feature.dist.mask)(branch=branch, index_url=index_url)
    versions = [package['version'] for package in repo_data if package['name'] == 'scalarizr']
    versions.sort(reverse=True)
    return versions[0]


@before.all
def verify_testenv():
    if CONF.scalr.branch:
        LOG.info('Run test in Test Env with branch: %s' % CONF.scalr.branch)
        sys.stdout.write('\x1b[1mPrepare Scalr environment\x1b[0m\n')
        resp = requests.post(
            'http://revizor2.scalr-labs.com/api/createContainer',
            data={'branch': CONF.scalr.branch}
        )
        LOG.debug('Resposne for container creation: %s' % resp.text)
        if resp.status_code != 200:
            raise AssertionError("Can't run container: %s" % resp.text)
        CONF.scalr.te_id = resp.json()['container_id']
        sys.stdout.write('\x1b[1mTest will run in this test environment:\x1b[0m http://%s.test-env.scalr.com\n\n' % CONF.scalr.te_id)


@before.all
def initialize_world():
    LOG.info('Save test start time')
    setattr(world, 'test_start_time', datetime.now())
    LOG.info('Initialize a Cloud object')
    c = Cloud()
    setattr(world, 'cloud', c)
    test_id = uuid.uuid4().get_hex()
    LOG.info('Test ID "%s"' % test_id)
    setattr(world, 'test_id', test_id)


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


@before.each_feature
def exclude_steps_by_options(feature):
    """
    Exclude steps from feature for @world.run_only_if
    """
    for scenario in feature.scenarios:
        steps_to_remove = set()
        for step in scenario.steps:
            func = step._get_match(None)[1].function
            if hasattr(func, '_exclude'):
                steps_to_remove.add(step)
        for step in steps_to_remove:
            scenario.steps.remove(step)
        if len(scenario.steps) == 0:
            feature.scenarios.remove(scenario)


@before.each_feature
def exclude_update_from_branch_to_stable(feature):
    """
    Exclude 'Update from branch to stable' scenario if branch version > 5.3 and stable < 5.4
    """
    if feature.name not in PKG_UPDATE_SUITES:
        return

    repo = "fatmouse"
    # Path to package versions excluded from test
    downgrade_blacklist_path = "agent/tasks/downgrade_blacklist.json"
    downgrade_content = ""
    downgrade_blacklist = list()
    excluded_scenario = "Update from branch to stable"

    try:
        git = GH.repos(ORG)(repo)
        downgrade_content = git.contents(downgrade_blacklist_path).get(ref=os.environ.get('RV_BRANCH')).content
    except github.ApiNotFoundError as e:
        LOG.error("Downgrade blacklist path not valid: [%s]" % e.message)
    if downgrade_content:
        downgrade_blacklist = map(itemgetter('version'), json.loads(b64decode(downgrade_content)))
    LOG.info('Packages downgrade blacklist: %s' % downgrade_blacklist)
    # get latest scalarizr ver for stable
    stable_ver = get_scalaraizr_latest_version('stable').rsplit('-1')[0]
    # get latest scalarizr ver for tested branch
    branch_ver = get_scalaraizr_latest_version(CONF.feature.branch).rsplit('-1')[0]
    LOG.info('Last package version from stable-[%s]; branch-[%s]' % (stable_ver, branch_ver))
    if LooseVersion(stable_ver) < LooseVersion('5.4') \
            and LooseVersion(branch_ver) > LooseVersion('5.3') \
            or stable_ver in downgrade_blacklist:
        scenario = filter(lambda s: s.name == excluded_scenario, feature.scenarios)[0]
        feature.scenarios.remove(scenario)
        LOG.info('Remove "%s" scenario from test suite  "%s"' % (scenario.name, feature.name))


@before.each_feature
def exclude_update_from_latest(feature):
    """
    Exclude 'update from latest' scenario if branch version is lower than latest
    """
    if feature.name in PKG_UPDATE_SUITES:
        branch = CONF.feature.branch
        if branch == 'latest':  # Excludes when trying to update from latest to latest
            match = True
        else:
            for br in [branch, 'latest']:
                last_version = get_scalaraizr_latest_version(br)
                if len(last_version.split('.')) == 3:
                    minor = int(last_version.split('.')[2][0])
                else:
                    minor = '0'
                if last_version.strip().endswith('-1'):
                    last_version = last_version.strip()[:-2]
                if br == branch:
                    to_version = last_version.split('.')[0] + '.' + last_version.split('.')[1] + '.' + str(minor)
                    LOG.debug("Testing branch version: %s" % to_version)
                else:
                    latest_version = last_version.split('.')[0] + '.' + last_version.split('.')[1] + '.' + str(minor)
                    LOG.debug("Latest version: %s" % latest_version)
            match = semver.match(latest_version, '>' + to_version)
        if match:
            scenario = [s for s in feature.scenarios if s.name == 'Update from latest to branch from ScalrUI'][0]
            feature.scenarios.remove(scenario)
            LOG.info("Removed scenario: %s" % scenario)


@after.outline
def get_logs_and_info_after_outline(*args, **kwargs):
    """Collect logs and additional info if outline failed"""
    scenario = args[0]
    outline_error = args[3]
    if scenario.name in OUTLINE_ITERATOR:
        OUTLINE_ITERATOR[scenario.name] += 1
    else:
        OUTLINE_ITERATOR[scenario.name] = 1
    if outline_error:
        get_all_logs_and_info(scenario, outline=str(OUTLINE_ITERATOR[scenario.name]), outline_failed=outline_error)


@after.each_scenario
def get_logs_and_info_after_scenario(scenario):
    """Give scalarizr_debug.log logs from servers"""
    get_all_logs_and_info(scenario)


@after.all
def cleanup_all(total):
    """If not have problem - stop farm and delete roles, vhosts, domains"""
    LOG.info('Failed steps: %s' % total.steps_failed)
    LOG.debug('Results %s' % total.scenario_results)
    LOG.debug('Passed %s' % total.scenarios_passed)
    if (not total.steps_failed and CONF.feature.stop_farm) or (CONF.feature.stop_farm and CONF.scalr.te_id):
        cloud_node = getattr(world, 'cloud_server', None)
        if cloud_node:
            LOG.info('Destroy node in cloud')
            try:
                cloud_node.destroy()
            except Exception as e:
                LOG.exception('Node %s can\'t be destroyed' % cloud_node.id)

        if getattr(world, 'farm', None) is None:
            return

        LOG.info('Clear and stop farm...')

        world.farm.terminate()
        IMPL.farm.clear_roles(world.farm.id)

        bundled_role_id = getattr(world, 'bundled_role_id', None)
        if bundled_role_id:
            LOG.info('Delete bundled role: %s' % bundled_role_id)
            try:
                IMPL.role.delete(bundled_role_id)
            except Exception as e:
                LOG.exception('Error on deletion role %s' % bundled_role_id)

        world.farm.vhosts.reload()
        if hasattr(world, 'vhosts_list'):
            for vhost in world.vhosts_list:
                LOG.info('Delete vhost: %s' % vhost.name)
                vhost.delete()

        try:
            world.farm.domains.reload()
            for domain in world.farm.domains:
                LOG.info('Delete domain: %s' % domain.name)
                domain.delete()
        except Exception as e:
            if 'You do not have permission to view this component' in e:
                LOG.warning('DNS disabled in Scalr config!')

        if world.farm.name.startswith('tmprev'):
            LOG.info('Delete working temporary farm')
            try:
                LOG.info('Wait all servers in farm terminated before delete')
                wait_until(world.farm_servers_state, args=('terminated',), timeout=1800,
                           error_text='Servers in farm not terminated too long')
                world.farm.destroy()
                world.farm = None
            except Exception as e:
                LOG.warning('Farm cannot be deleted: %s' % str(e))

        if CONF.feature.platform.is_ec2:
            try:
                wait_until(world.farm_servers_state, args=('terminated',),
                           timeout=1800, error_text=('Servers in farm have no status terminated'))
            except Exception as e:
                LOG.error('Servers in farms are not terminated after 1800 seconds!')
            for volume in world.cloud._driver.list_volumes(filters={'tag-value': getattr(world, 'test_id')}):
                LOG.debug('Try delete volume "%s"' % volume.id)
                try:
                    volume.destroy()
                except Exception as e:
                    LOG.warning('Volume "%s" can\'t be deleted: %s' % (volume.id, str(e)))
            for sn in world.cloud._driver.list_snapshots(filters={'tag-value': getattr(world, 'test_id')}):
                LOG.debug('Try delete snapshot "%s"' % sn.id)
                try:
                    sn.destroy()
                except Exception as e:
                    LOG.warning('Snapshot "%s" can\'t be deleted: %s' % (sn.id, str(e)))

    else:
        LOG.info('Setup a long timeouts for all roles in farm')
        if getattr(world, 'farm', None) is None:
            return
        world.farm.roles.reload()
        for r in world.farm.roles:
            IMPL.farm.edit_role(world.farm.id, r.role_id, options={"system.timeouts.reboot": 999999,
                                                                   "system.timeouts.launch": 999999})
    for v in dir(world):
        if isinstance(getattr(world, v), ExtendedNode):
            world.__delattr__(v)

    # Cleanup Azure resources
    if CONF.feature.platform.is_azure:
        cloud = getattr(world, 'cloud', Cloud())
        cloud._driver.resources_cleaner()
