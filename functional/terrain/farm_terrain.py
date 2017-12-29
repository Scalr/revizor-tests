__author__ = 'gigimon'
import os
import re
import time
import json
import logging

from lettuce import world, step

from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.api import Script, Metrics, ChefServer
from revizor2.consts import DATABASE_BEHAVIORS, Dist
from revizor2.defaults import DEFAULT_ROLE_OPTIONS, DEFAULT_STORAGES, \
    DEFAULT_ADDITIONAL_STORAGES, DEFAULT_ORCHESTRATION_SETTINGS, \
    SMALL_ORCHESTRATION_LINUX, SMALL_ORCHESTRATION_WINDOWS, DEFAULT_WINDOWS_ADDITIONAL_STORAGES, DEFAULT_SCALINGS, \
    DEFAULT_CHEF_SOLO, DEFAULT_CHEF_SOLO_URL, DEFAULT_ANSIBLE_TOWER


LOG = logging.getLogger(__name__)


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_farm(launched=True)


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
    """Clear all roles from farm and stop farm"""
    world.give_empty_farm(launched=False)


@step(r"I add(?P<behavior> \w+-?\w+?)? role(?P<saved_role> [\w\d]+)? to this farm(?: with (?P<options>[ \w\d,-]+))?(?: as (?P<alias>[\w\d]+))?")
def add_role_to_farm(step, behavior=None, saved_role=None, options=None, alias=None):
    additional_storages = None
    scripting = None
    role_id = None
    scaling_metrics = None
    options = options or []
    role_options = dict()
    old_branch = CONF.feature.branch
    default_role_options = DEFAULT_ROLE_OPTIONS.copy()
    role_options.update(default_role_options['hostname'])
    platform = CONF.feature.platform
    if CONF.feature.dist.id == 'scientific-6-x' or \
            (CONF.feature.dist.id == 'centos-7-x' and platform.is_ec2):
        default_role_options['noiptables'] = {"base.disable_firewall_management": False}

    if CONF.feature.dist.is_windows:
        role_options["base.reboot_after_hostinit_phase"] = "1"

    if saved_role:
        role_id = getattr(world, '%s_id' % saved_role.strip())
    if not behavior:
        behavior = os.environ.get('RV_BEHAVIOR', 'base')
    else:
        behavior = behavior.strip()
    if options:
        for opt in [o.strip() for o in options.strip().split(',')]:
            LOG.info('Inspect option: %s' % opt)
            if opt == 'noiptables' and (platform.is_cloudstack or platform.is_rackspacengus):
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
                script_sleep_10 = Script.get_id('Sleep 10')['id']
                scripts = {'SCRIPT_PONG_ID': script_pong_id,
                           'SCRIPT_INIT_ID': script_init_id,
                           'SCRIPT_SLEEP_10': script_sleep_10}
                scripting = json.loads(DEFAULT_ORCHESTRATION_SETTINGS % scripts)
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
                script_id = Script.get_id('Multiplatform exit 1')['id']
                scripting = [
                    {
                        "scope": "farmrole",
                        "action": "add",
                        "timeout": "1200",
                        "isSync": True,
                        "orderIndex": 10,
                        "type": "scalr",
                        "isActive": True,
                        "eventName": "BeforeHostUp",
                        "target": {
                            "type": "server"
                        },
                        "isFirstConfiguration": None,
                        "scriptId": script_id,
                        "scriptName": "Multiplatform exit 1",
                        "scriptOs": "windows" if CONF.feature.dist.is_windows else "linux",
                        "version": -1,
                        "scriptPath": "",
                        "runAs": ""
                    }
                ]
                role_options.update(default_role_options.get(opt, {}))

            elif opt == 'apachefix':
                script_id = Script.get_id('CentOS7 fix apache log')['id']
                scripting = [
                    {
                        "scope": "farmrole",
                        "action": "add",
                        # id: extModel123
                        # eventOrder 2
                        "timeout": "1200",
                        "isSync": True,
                        "orderIndex": 10,
                        "type": "scalr",
                        "isActive": True,
                        "eventName": "HostInit",
                        "target": {
                            "type": "server"
                        },
                        "isFirstConfiguration": None,
                        "scriptId": script_id,
                        "scriptName": "CentOS7 fix apache log",
                        "scriptOs": "linux",
                        "version": -1,
                        "scriptPath": "",
                        "runAs": ""
                    }
                ]
            elif opt == 'storages':
                LOG.info('Insert additional storages config')
                if CONF.feature.dist.is_windows:
                    additional_storages = {
                        'configs': DEFAULT_WINDOWS_ADDITIONAL_STORAGES.get(
                            platform.cloud_family, [])}
                else:
                    if platform.is_rackspacengus:
                        additional_storages = {'configs': DEFAULT_ADDITIONAL_STORAGES.get(platform.RACKSPACENGUS, [])}
                    else:
                        additional_storages = {'configs': DEFAULT_ADDITIONAL_STORAGES.get(platform.cloud_family, [])}
                    if platform.is_ec2 and CONF.feature.dist.id in ['centos-6-x', 'ubuntu-14-04']:
                        additional_storages['configs'].append({
                            "id": None,
                            "type": "raid.ebs",
                            "fs": "ext3",
                            "settings": {
                                "raid.level": "1",
                                "raid.volumes_count": 2,
                                "ebs.size": "1",
                                "ebs.type": "standard"
                            },
                            "mount": True,
                            "mountPoint": "/media/raidmount",
                            "reUse": True,
                            "status": "",
                        })

            elif opt == 'ephemeral':
                if platform.is_ec2 and CONF.feature.dist.is_windows:
                    eph_disk_conf = {
                        "type": "ec2_ephemeral",
                        "reUse": False,
                        "settings": {
                            "ec2_ephemeral.name": "ephemeral0",
                            "ec2_ephemeral.size": "4"
                        },
                        "status": "",
                        "isRootDevice": False,
                        "readOnly": False,
                        "category": "Ephemeral storage",
                        "fs": "ntfs",
                        "mount": True,
                        "rebuild": False,
                        "mountPoint": "Z",
                        "label": "test_label"}
                    additional_storages = {'configs': [eph_disk_conf]}
            elif opt == 'unmanaged':
                if not CONF.feature.dist.is_windows and platform.is_azure:
                    eph_disk_conf = {
                        "reUse": True,
                        "type": "azure_vhd",
                        "settings": {
                            "azure_vhd.type": "Standard_LRS",
                            "azure_vhd.storage_account": "/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/"
                                                         "resourceGroups/revizor/providers/Microsoft.Storage/"
                                                         "storageAccounts/revizor",
                            "azure_vhd.size": "1"
                        },
                        "status": "",
                        "isRoot": "0",
                        "readOnly": False,
                        "category": " Persistent storage",
                        "fs": "ext3",
                        "mount": True,
                        "mountPoint": "/media/diskmount",
                        "mountOptions": "",
                        "rebuild": True
                    }
                    additional_storages = {'configs': [eph_disk_conf]}
                    role_options["azure.storage-account"] = "/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/" \
                                                            "resourceGroups/revizor/providers/Microsoft.Storage/" \
                                                            "storageAccounts/revizor"
            elif opt == 'ansible-tower':
                default_at_opts = DEFAULT_ANSIBLE_TOWER.copy()
                if CONF.feature.dist.is_windows:
                    default_at_opts.update({"base.ansibletower.inventory": "33"})
                role_options.update(default_at_opts)

            elif opt == 'scaling':
                scaling_metrics = {Metrics.get_id('revizor') or Metrics.add(): {'max': '', 'min': ''}}
                LOG.info('Insert scaling metrics options %s' % scaling_metrics)
            elif opt == 'prepare_scaling_linux':
                script_id = Script.get_id('Revizor scaling prepare linux')['id']
                scripting = [
                    {
                        "scope": "farmrole",
                        "action": "add",
                        # id: extModel123
                        # eventOrder 2
                        "timeout": "1200",
                        "isSync": True,
                        "orderIndex": 10,
                        "type": "scalr",
                        "isActive": True,
                        "eventName": "HostInit",
                        "target": {
                            "type": "server"
                        },
                        "isFirstConfiguration": None,
                        "scriptId": script_id,
                        "scriptName": "Revizor scaling prepare linux",
                        "scriptOs": "linux",
                        "version": -1,
                        "scriptPath": "",
                        "runAs": ""
                    }
                ]
            elif opt == 'prepare_scaling_win':
                script_id = Script.get_id('Revizor scaling prepare windows')['id']
                scripting = [
                    {
                        "scope": "farmrole",
                        "action": "add",
                        # id: extModel123
                        # eventOrder 2
                        "timeout": "1200",
                        "isSync": True,
                        "orderIndex": 10,
                        "type": "scalr",
                        "isActive": True,
                        "eventName": "HostInit",
                        "target": {
                            "type": "server"
                        },
                        "isFirstConfiguration": None,
                        "scriptId": script_id,
                        "scriptName": "Revizor scaling prepare windows",
                        "scriptOs": "windows",
                        "version": -1,
                        "scriptPath": "",
                        "runAs": ""
                    }
                ]
            elif opt.startswith('scaling'):
                metric_name = DEFAULT_SCALINGS[opt]
                metric_id = Metrics.get_id(metric_name)
                scaling_metrics = {
                    metric_id: {
                        "max": "75",
                        "min": "50"
                        }
                    }
            elif 'chef-solo' in opt:
                chef_opts = opt.split('-')
                default_chef_solo_opts = DEFAULT_CHEF_SOLO.copy()
                # Set common arguments
                repo_url = DEFAULT_CHEF_SOLO_URL.get(chef_opts[2], '')
                chef_attributes = json.dumps({'chef-solo': {'result': opt.strip()}})
                private_key = ''
                relative_path = ''
                # Set arguments for repo url with branch
                if chef_opts[-1] == 'branch':
                    repo_url = ''.join((repo_url, '@revizor-test'))
                # Set arguments for private repo
                elif chef_opts[2] == 'private':
                    relative_path = 'cookbooks'
                    private_key = open(CONF.ssh.private_key, 'r').read()
                # Update default chef_solo options
                default_chef_solo_opts.update({
                    "chef.cookbook_url": repo_url,
                    "chef.relative_path": relative_path,
                    "chef.ssh_private_key": private_key,
                    "chef.attributes": chef_attributes})
                # Update role options
                role_options.update(default_chef_solo_opts)
            elif 'chef' in opt and CONF.feature.dist.id != Dist('coreos').id:
                option = default_role_options.get(opt, {})
                if option:
                    option['chef.server_id'] = ChefServer.get('https://api.opscode.com/organizations/webta').id
                role_options.update(option)
            else:
                LOG.info('Insert configs for %s' % opt)
                role_options.update(default_role_options.get(opt, {}))
    if behavior == 'rabbitmq':
        del(role_options['hostname.template'])
    if behavior == 'redis':
        LOG.info('Insert redis settings')
        role_options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                             'db.msr.redis.use_password': True})
    if behavior in DATABASE_BEHAVIORS:
        storages = DEFAULT_STORAGES.get(platform.name, None)
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
    if CONF.feature.platform.is_cloudstack: #Maybe use on all cloudstack
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I add to farm imported role$')
def add_new_role_to_farm(step):
    options = getattr(world, 'role_options', {})
    bundled_role = Role.get(world.bundled_role_id)
    world.farm.add_role(
        world.bundled_role_id,
        options=options,
        alias=bundled_role.name)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, '%s_role' % role.alias, role)


@step('I suspend farm')
def farm_state_suspend(step):
    """Suspend farm"""
    world.farm.suspend()


@step('I resume farm')
def farm_resume(step):
    """Resume farm"""
    world.farm.resume()


@step('I wait farm in ([\w]+) state')
def wait_for_farm_state(step, state):
    """Wait for state of farm"""
    wait_until(world.get_farm_state, args=(
        state, ), timeout=300, error_text=('Farm have no status %s' % state))
