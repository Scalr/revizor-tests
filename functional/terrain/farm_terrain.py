__author__ = 'gigimon'
import os
import re
import time
import json
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.backend import IMPL
from revizor2.api import Script, Farm, Metrics
from revizor2.consts import Platform, DATABASE_BEHAVIORS
from revizor2.defaults import DEFAULT_ROLE_OPTIONS, DEFAULT_STORAGES, \
    DEFAULT_ADDITIONAL_STORAGES, DEFAULT_ORCHESTRATION_SETTINGS, \
    SMALL_ORCHESTRATION_LINUX, SMALL_ORCHESTRATION_WINDOWS, DEFAULT_WINDOWS_ADDITIONAL_STORAGES


LOG = logging.getLogger(__name__)


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_running_farm()


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
    """Clear all roles from farm and stop farm"""
    world.farm = Farm.get(CONF.main.farm_id)
    IMPL.farm.clear_roles(world.farm.id)
    LOG.info('Clear farm')
    if world.farm.running:
        LOG.info('Terminate farm %s' % world.farm.id)
        world.farm.terminate()


@step(r"I add(?P<behavior> \w+)? role(?P<saved_role> [\w\d]+)? to this farm(?: with (?P<options>[ \w\d,-]+))?(?: as (?P<alias>[\w\d]+))?")
def add_role_to_farm(step, behavior=None, saved_role=None, options=None, alias=None):
    additional_storages = None
    options = options or []
    scripting = None
    role_id = None
    scaling_metrics = None
    old_branch = CONF.feature.branch
    role_options = {
        "base.hostname_format": "{SCALR_FARM_NAME}-{SCALR_ROLE_NAME}-{SCALR_INSTANCE_INDEX}"
    }

    if CONF.feature.dist.startswith('win'):
        role_options["base.hostname_format"] = "{SCALR_FARM_NAME}"

    if saved_role:
        role_id = getattr(world, '%s_id' % saved_role.strip())
    if not behavior:
        behavior = os.environ.get('RV_BEHAVIOR', 'base')
    else:
        behavior = behavior.strip()
    if options:
        for opt in [o.strip() for o in options.strip().split(',')]:
            LOG.info('Inspect option: %s' % opt)
            if opt == 'noiptables' and CONF.feature.driver.current_cloud in [Platform.IDCF, Platform.CLOUDSTACK]:
                continue
            if opt in ('branch_latest', 'branch_stable'):
                CONF.feature.branch = opt.split('_')[1]
            if 'redis processes' in opt:
                redis_count = re.findall(r'(\d+) redis processes', options)[0].strip()
                LOG.info('Setup %s redis processes' % redis_count)
                role_options.update({'db.msr.redis.num_processes': int(redis_count)})
            elif opt == 'orchestration':
                LOG.info('Setup scripting options')
                script_pong_id = Script.get_id('Linux ping-pong')['id']
                script_init_id = Script.get_id('Revizor orchestration init')['id']
                scripting = json.loads(DEFAULT_ORCHESTRATION_SETTINGS % {'SCRIPT_PONG_ID': script_pong_id,
                                                                         'SCRIPT_INIT_ID': script_init_id})
            elif opt == 'small_linux_orchestration':
                LOG.debug('Add small orchestration for linux')
                script_pong_id = Script.get_id('Linux ping-pong')['id']
                script_last_reboot_id = Script.get_id('Revizor last reboot')['id']
                scripting = json.loads(SMALL_ORCHESTRATION_LINUX % {'SCRIPT_PONG_ID': script_pong_id,
                                                                    'SCRIPT_LAST_REBOOT_ID': script_last_reboot_id})

            elif opt == 'small_win_orchestration':
                LOG.debug('Add small orchestration for windows')

                script_pong_cmd_id = Script.get_id('Windows ping-pong. CMD')['id']
                script_pong_ps_id = Script.get_id('Windows ping-pong. PS')['id']
                scripting = json.loads(SMALL_ORCHESTRATION_WINDOWS % {'SCRIPT_PONG_CMD_ID': script_pong_cmd_id,
                                                                      'SCRIPT_PONG_PS_ID': script_pong_ps_id})

            elif opt == 'failed_script':
                script_id = Script.get_id('test_return_nonzero')['id']
                scripting = [
                    {
                        "script_type": "scalr",
                        "script_id": script_id,
                        "script": "test_return_nonzero",
                        "os": "linux",
                        "event": "BeforeHostUp",
                        "target": "instance",
                        "isSync": "1",
                        "timeout": "1200",
                        "version": "-1",
                        "params": {},
                        "order_index": "10",
                        "system": "",
                        "script_path": "",
                        "run_as": "root"
                    }
                ]
                role_options.update(DEFAULT_ROLE_OPTIONS.get(opt, {}))

            elif opt == 'apachefix':
                script_id = Script.get_id('CentOS7 fix apache log')['id']
                scripting = [
                    {
                        "script_type": "scalr",
                        "script_id": script_id,
                        "script": "CentOS7 fix apache log",
                        "os": "linux",
                        "event": "HostInit",
                        "target": "instance",
                        "isSync": "1",
                        "timeout": "1200",
                        "version": "-1",
                        "params": {},
                        "order_index": "20",
                        "system": "",
                        "script_path": "",
                        "run_as": "root"
                    }
                ]
            elif opt == 'storages':
                LOG.info('Insert additional storages config')
                if CONF.feature.dist.startswith('win'):
                    additional_storages = {
                        'configs': DEFAULT_WINDOWS_ADDITIONAL_STORAGES.get(
                            CONF.feature.driver.cloud_family, [])}
                else:
                    if CONF.feature.driver.current_cloud == Platform.RACKSPACE_US:
                        additional_storages = {'configs': DEFAULT_ADDITIONAL_STORAGES.get(Platform.RACKSPACE_US, [])}
                    else:
                        additional_storages = {'configs': DEFAULT_ADDITIONAL_STORAGES.get(CONF.feature.driver.cloud_family, [])}
            elif opt == 'scaling':
                scaling_metrics = {Metrics.get_id('revizor') or Metrics.add(): {'max': '', 'min': ''}}
                LOG.info('Insert scaling metrics options %s' % scaling_metrics)
            else:
                LOG.info('Insert configs for %s' % opt)
                role_options.update(DEFAULT_ROLE_OPTIONS.get(opt, {}))
    if behavior == 'rabbitmq':
        del(role_options['base.hostname_format'])
    if behavior == 'redis':
        LOG.info('Insert redis settings')
        role_options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                             'db.msr.redis.use_password': True})
    if behavior in DATABASE_BEHAVIORS:
        storages = DEFAULT_STORAGES.get(CONF.feature.driver.current_cloud, None)
        if storages:
            LOG.info('Insert main settings for %s storage' % CONF.feature.storage)
            role_options.update(storages.get(CONF.feature.storage, {}))
    LOG.debug('All farm settings: %s' % role_options)
    role = world.add_role_to_farm(behavior, options=role_options, scripting=scripting,
                                  storages=additional_storages, alias=alias,
                                  role_id=role_id, scaling=scaling_metrics)
    LOG.debug('Save role object with name %s' % role.alias)
    setattr(world, '%s_role' % role.alias, role)
    if 'branch_latest' in options or 'branch_stable' in options:
        CONF.feature.branch = old_branch


@step('I delete (\w+) role from this farm')
def delete_role_from_farm(step, role_type):
    LOG.info('Delete role %s from farm' % role_type)
    role = world.get_role(role_type)
    world.farm.delete_role(role.role_id)


@step('I (?:terminate|stop) farm')
def farm_terminate(step):
    """Terminate (stopping) farm"""
    world.farm.terminate()
    time.sleep(30)


@step('I start farm$')
def farm_launch(step):
    """Start farm"""
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I start farm with delay$')
def farm_launch(step):
    """Start farm with delay for cloudstack"""
    if CONF.feature.driver.current_cloud == Platform.IDCF: #Maybe use on all cloudstack
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))