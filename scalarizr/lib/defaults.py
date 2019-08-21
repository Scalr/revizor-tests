import re

from revizor2.conf import CONF
from revizor2.consts import Dist, Platform
from revizor2.helpers import farmrole


class Defaults(object):
    @staticmethod
    def apply_option(params, opt):
        opt = re.sub('[^\w]', '_', opt)
        method = 'set_' + opt
        if not hasattr(Defaults, method):
            raise NotImplementedError('Option "%s" is not supported for farm role' % opt)
        getattr(Defaults, method)(params)

    @staticmethod
    def set_efs_storages(params, linked_services):
        params.storage.volumes = [
                farmrole.Volume(
                    mount='/media/efsmount',
                    fs='nfs',
                    re_build=False,
                    re_use=False,
                    category='Persistent storage',
                    engine='efs',
                    linked_services=linked_services)
            ]

    @staticmethod
    def set_storages(params):
        if CONF.feature.dist.is_windows:
            Defaults.set_storages_windows(params)
        else:
            Defaults.set_storages_linux(params)

    @staticmethod
    def set_storages_windows(params):
        if CONF.feature.platform.is_cloudstack:
            params.storage.volumes = [
                farmrole.Volume(size=1, fs='ntfs', type='custom')
            ]
        elif not CONF.feature.platform.is_rackspacengus:
            params.storage.volumes = [
                farmrole.Volume(size=2, fs='ntfs', mount='F'),
                farmrole.Volume(size=1, fs='ntfs', mount='E', label='test_label')
            ]
        if CONF.feature.platform in [Platform.EC2, Platform.GCE, Platform.AZURE]:
            params.storage.volumes.append(
                params.storage,
                farmrole.Volume(size=3, fs='ntfs', mount='C:\diskmount')
            )

    @staticmethod
    def set_storages_linux(params):
        if CONF.feature.platform.is_rackspacengus:
            return
        if CONF.feature.platform in [Platform.AZURE, Platform.EC2]:
            params.storage.volumes = [
                farmrole.Volume(size=1, mount='/media/diskmount', re_build=True),
                farmrole.Volume(size=1, mount='/media/partition', re_build=True)
            ]

        else:
            params.storage.volumes = [
                farmrole.Volume(size=1, mount='/media/diskmount', re_build=True)
            ]

    @staticmethod
    def set_db_storage(params):
        if CONF.feature.platform.is_ec2:
            Defaults.set_db_storage_ec2(params)
        elif CONF.feature.platform.is_gce:
            Defaults.set_db_storage_gce(params)
        elif CONF.feature.platform.is_openstack:
            Defaults.set_db_storage_openstack(params)
        elif CONF.feature.platform.is_rackspacengus:
            Defaults.set_db_storage_rackspacengus(params)

    @staticmethod
    def set_db_storage_ec2(params):
        if CONF.feature.storage == 'persistent':
            params.database.storage = farmrole.DataStorage()
        elif CONF.feature.storage == 'lvm':
            params.database.storage = farmrole.DataStorage(engine='lvm', type='ephemeral0', mount='Z')
        elif CONF.feature.storage == 'eph':
            params.database.storage = farmrole.DataStorage(engine='eph', type='/dev/sda2')

    @staticmethod
    def set_db_storage_gce(params):
        if CONF.feature.storage == 'persistent':
            params.database.storage = farmrole.DataStorage()
        elif CONF.feature.storage == 'eph':
            params.database.storage = farmrole.DataStorage(engine='eph', type='ephemeral-disk-0')

    @staticmethod
    def set_db_storage_openstack(params):
        if CONF.feature.storage == 'persistent':
            params.database.storage = farmrole.DataStorage()

    @staticmethod
    def set_db_storage_rackspacengus(params):
        if CONF.feature.storage == 'persistent':
            params.database.storage = farmrole.DataStorage(size=100)
        elif CONF.feature.storage == 'eph':
            params.database.storage = farmrole.DataStorage(engine='eph', type='/dev/loop0')

    @staticmethod
    def set_ephemeral(params):
        if CONF.feature.platform.is_ec2 and CONF.feature.dist.is_windows:
            params.storage.volumes = [
                farmrole.Volume(size=4, engine='eph', type='ephemeral0', fs='ntfs', mount='Z',
                                label='test_label', category='Ephemeral storage', re_use=False)
            ]

    @staticmethod
    def set_unmanaged(params):
        if not CONF.feature.dist.is_windows and CONF.feature.platform.is_azure:
            params.azure.storage_account = CONF.feature.platform.storage_account
            params.storage.volumes = [
                farmrole.Volume(engine='unmanaged', mount='/media/diskmount', re_build=True)
            ]

    @staticmethod
    def set_chef(params):
        if CONF.feature.dist.id != Dist('coreos').id:
            params.bootstrap_with_chef.enabled = True
            params.bootstrap_with_chef.server = farmrole.ChefServer(
                url='https://api.opscode.com/organizations/webta')
            params.bootstrap_with_chef.runlist = '["recipe[memcached::default]", "recipe[revizorenv]"]'
            params.bootstrap_with_chef.attributes = '{"memcached": {"memory": "1024"}}'
            params.bootstrap_with_chef.daemonize = True
            params.bootstrap_with_chef.client_rb_template = "verbose_logging false\nlockfile '/var/chef/lock'"
            params.bootstrap_with_chef.log_level = "fatal"

    @staticmethod
    def set_chef_role(params):
        if CONF.feature.dist.id != Dist('coreos').id:
            params.bootstrap_with_chef.enabled = True
            params.bootstrap_with_chef.server = farmrole.ChefServer(
                url='https://api.opscode.com/organizations/webta')
            params.bootstrap_with_chef.role_name = 'test_chef_role'
            params.bootstrap_with_chef.daemonize = True

    @staticmethod
    def set_chef_fail(params):
        if CONF.feature.dist.id != Dist('coreos').id:
            params.bootstrap_with_chef.enabled = True
            params.bootstrap_with_chef.server = farmrole.ChefServer(
                url='https://api.opscode.com/organizations/webta')
            params.bootstrap_with_chef.runlist = '["role[always_fail]"]'
            params.bootstrap_with_chef.daemonize = True

    @staticmethod
    def set_chef_hostname(params, chef_host_name):
        if CONF.feature.dist.id != Dist('coreos').id:
            params.bootstrap_with_chef.enabled = True
            params.bootstrap_with_chef.server = farmrole.ChefServer(url='https://api.opscode.com/organizations/webta')
            params.bootstrap_with_chef.runlist = '["recipe[set_hostname_attr::default]"]'
            params.bootstrap_with_chef.daemonize = True
            params.bootstrap_with_chef.attributes = f'{{"new_hostname": "{chef_host_name}"}}'
            params.network.hostname_template = ''

    @staticmethod
    def set_winchef(params):
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.server = farmrole.ChefServer(
            url='https://api.opscode.com/organizations/webta')
        params.bootstrap_with_chef.runlist = '["recipe[windows_file_create::default]", "recipe[revizorenv]", ' \
                                             '"recipe[revizor_chef_multi::default]"]'
        params.bootstrap_with_chef.attributes = '{"revizor_chef_multi": {"result": "changed_result"}}'

    @staticmethod
    def set_winchef_role(params):
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.server = farmrole.ChefServer(
            url='https://api.opscode.com/organizations/webta')
        params.bootstrap_with_chef.role_name = 'test_chef_role_windows'

    @staticmethod
    def set_chef_solo(params, options):
        chef_opts = options.split('-')
        url_type = 'git'
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.runlist = '["recipe[revizor-chef]"]'
        params.bootstrap_with_chef.attributes = '{"chef-solo":{"result":"%s"}}' % options.strip()
        params.bootstrap_with_chef.solo_rb_template = "lockfile '/var/chef/lock'"
        if chef_opts[2] == 'private':
            url = 'git@github.com:Scalr/int-cookbooks.git'
            params.bootstrap_with_chef.path = 'cookbooks'
            params.bootstrap_with_chef.private_key = CONF.ssh.private_key.read_text()
        elif chef_opts[2] == 'custom_url':
            url = 'https://cookbooks.msk.scalr.net/cookbooks.zip'
            url_type = 'http'
        else:
            url = 'https://github.com/Scalr/sample-chef-repo.git'
        if chef_opts[-1] == 'branch':
            url = ''.join((url, '@revizor-test'))
        params.bootstrap_with_chef.cookbook_url = url
        params.bootstrap_with_chef.url_type = url_type

    @staticmethod
    def set_noiptables(params):
        if not CONF.feature.platform.is_cloudstack and not CONF.feature.platform.is_rackspacengus:
            params.advanced.disable_iptables_mgmt = True

    @staticmethod
    def set_deploy(params):
        pass
        # "dm.application_id": "217",
        # "dm.remote_path": "/var/www/pecha"

    @staticmethod
    def set_branch_custom(params):
        params.development.scalarizr_branch = CONF.feature.to_branch

    @staticmethod
    def set_failed_script(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='BeforeHostUp', script='Multiplatform exit 1')
        ]
        params.advanced.abort_init_on_script_fail = True

    @staticmethod
    def set_init_reboot(params):
        params.advanced.reboot_after_hostinit = True

    @staticmethod
    def set_failed_hostname(params):
        params.network.hostname_template = 'r{REVIZOR_FAILED_HOSTNAME}'

    @staticmethod
    def set_hostname(params):
        params.network.hostname_source = 'template'
        params.network.hostname_template = 'r{SCALR_FARM_ID}-{SCALR_FARM_ROLE_ID}-{SCALR_INSTANCE_INDEX}'

    @staticmethod
    def set_termination_preferences(params):
        params.scaling.scaling_behavior = 'suspend'
        params.scaling.consider_suspended = 'terminated'

    @staticmethod
    def set_apachefix(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='CentOS7 fix apache log')
        ]

    @staticmethod
    def set_orchestration(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='Revizor orchestration init'),
            farmrole.OrchestrationRule(event='HostInit', script='/tmp/script.sh'),
            farmrole.OrchestrationRule(event='HostInit', script='https://gist.githubusercontent.com/gigimon'
                                                                '/f86c450f4620be2315ea/raw'
                                                                '/09cc205dd5552cb56c5d542b420ee1fe9f2838e1'
                                                                '/gistfile1.txt'),
            farmrole.OrchestrationRule(event='BeforeHostUp', script='Linux ping-pong'),
            farmrole.OrchestrationRule(event='BeforeHostUp',
                                       cookbook_url='git@github.com:Scalr/int-cookbooks.git',
                                       runlist='["recipe[revizor-chef::default]"]',
                                       path='cookbooks'),
            farmrole.OrchestrationRule(event='HostUp', script='https://gist.githubusercontent.com/Theramas'
                                                              '/5b2a9788df316606f72883ab1c3770cc/raw'
                                                              '/3ae1a3f311d8e43053fbd841e8d0f17daf1d5d66'
                                                              '/multiplatform'),
            farmrole.OrchestrationRule(event='HostUp', script='Linux ping-pong', run_as='revizor2'),
            farmrole.OrchestrationRule(event='HostUp', script='/home/revizor/local_script.sh', run_as='revizor'),
            farmrole.OrchestrationRule(event='HostUp', script='Linux ping-pong', run_as='revizor'),
            farmrole.OrchestrationRule(event='HostUp', runlist='["recipe[create_file::default]"]',
                                       attributes='{"create_file":{"path":"/root/chef_hostup_result"}}'),
            farmrole.OrchestrationRule(event='HostUp', script='/bin/uname'),
            farmrole.OrchestrationRule(event='HostUp', script='Sleep 10', timeout=5),
            farmrole.OrchestrationRule(event='HostUp', script='Git_scripting_orchestration')
        ]

    @staticmethod
    def set_small_linux_orchestration(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='Revizor last reboot'),
            farmrole.OrchestrationRule(event='HostUp', script='Revizor last reboot')
        ]

    @staticmethod
    def set_small_win_orchestration(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='Windows ping-pong. CMD'),
            farmrole.OrchestrationRule(event='HostUp', script='Windows ping-pong. CMD'),
            farmrole.OrchestrationRule(event='HostUp', script='Git_scripting_orchestration')
        ]

    @staticmethod
    def set_scaling(params):
        params.scaling.rules = [farmrole.ScalingRule.get_or_create_metric(max=75, min=50)]

    @staticmethod
    def set_scaling_execute_linux(params):
        params.scaling.rules = [
            farmrole.ScalingRule(metric='RevizorLinuxExecute', max=75, min=50)
        ]

    @staticmethod
    def set_scaling_read_linux(params):
        params.scaling.rules = [
            farmrole.ScalingRule(metric='RevizorLinuxRead', max=75, min=50)
        ]

    @staticmethod
    def set_scaling_execute_win(params):
        params.scaling.rules = [
            farmrole.ScalingRule(metric='RevizorWindowsExecute', max=75, min=50)
        ]

    @staticmethod
    def set_scaling_read_win(params):
        params.scaling.rules = [
            farmrole.ScalingRule(metric='RevizorWindowsRead', max=75, min=50)
        ]

    @staticmethod
    def set_prepare_scaling_linux(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='Revizor scaling prepare linux')
        ]

    @staticmethod
    def set_prepare_scaling_win(params):
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostInit', script='Revizor scaling prepare windows')
        ]

    @staticmethod
    def set_docker(params):
        params.orchestration.rules.append(
            params.orchestration,
            farmrole.OrchestrationRule(event='HostInit', script='https://get.docker.com')
        )

    @staticmethod
    def set_long_variables(params: farmrole.FarmRoleParams):
        params.global_variables.variables = [
            *[farmrole.Variable(name='rev_long_var_%s' % i, value='a' * 4095) for i in range(6)],
            farmrole.Variable(name='rev_very_long_var', value='a' * 8192),
            farmrole.Variable(name='rev_nonascii_var', value='ревизор')
        ]

    @staticmethod
    def set_ansible_tower(params, context):
        credentials_name = context['credentials_name']
        pk = context[f'at_cred_primary_key_{credentials_name}']
        boot_config_name = ''.join((credentials_name, str(pk)))
        at_configuration_id = context['at_configuration_id']
        params.bootstrap_with_at.enabled = True
        params.bootstrap_with_at.hostname = 'publicIp'
        params.bootstrap_with_at.configurations = [
            farmrole.AnsibleTowerConfiguration(id=at_configuration_id, name=boot_config_name, variables='')
        ]

    @staticmethod
    def set_ansible_orchestration(params, context):
        at_configuration_id = context['at_configuration_id']
        job_template_id = context['job_template_id']
        at_python_path = ''
        if not CONF.feature.dist.is_windows:
            at_python_path = ''.join((context['at_python_path'], '\n'))
        params.orchestration.rules = [
            farmrole.OrchestrationRule(event='HostUp', configuration=at_configuration_id,
                                       jobtemplate=job_template_id,
                                       variables=at_python_path + 'dir2: Extra_Var_HostUp'),
            farmrole.OrchestrationRule(event='RebootComplete', configuration=at_configuration_id,
                                       jobtemplate=job_template_id,
                                       variables=at_python_path + 'dir2: Extra_Var_RebootComplete'),
            farmrole.OrchestrationRule(event='ResumeComplete', configuration=at_configuration_id,
                                       jobtemplate=job_template_id,
                                       variables=at_python_path + 'dir2: Extra_Var_ResumeComplete')
        ]

