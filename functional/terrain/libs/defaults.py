from revizor2.conf import CONF
from revizor2.consts import Dist
from revizor2.helpers import farmrole


class Defaults(object):
    @staticmethod
    def apply_option(params, opt):
        method = 'set_' + opt
        if hasattr(Defaults, method):
            getattr(Defaults, method)(params)

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
        else:
            params.storage.volumes = [
                farmrole.Volume(size=2, fs='ntfs', mount='D'),
                farmrole.Volume(size=2, fs='ntfs', mount='E', label='test_label2')  # TODO: label impl
            ]

    @staticmethod
    def set_storages_linux(params):
        params.storage.volumes = [
            farmrole.Volume(size=1, mount='/media/diskmount', re_build=True),
            farmrole.Volume(size=1, mount='/media/partition', re_build=True)
        ]
        if CONF.feature.platform.is_cloudstack:
            params.storage.volumes.append(
                farmrole.Volume(size=1, engine='raid', level=10, volumes=4, mount='/media/raidmount')
            )

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
        elif CONF.feature.storage == 'raid10':
            params.database.storage = farmrole.DataStorage(engine='raid', level=10, volumes=4)
        elif CONF.feature.storage == 'raid5':
            params.database.storage = farmrole.DataStorage(engine='raid', level=5, volumes=3)
        elif CONF.feature.storage == 'raid1':
            params.database.storage = farmrole.DataStorage(engine='raid', level=1, volumes=2)
        elif CONF.feature.storage == 'raid0':
            params.database.storage = farmrole.DataStorage(engine='raid', level=0, volumes=2)

    @staticmethod
    def set_db_storage_gce(params):
        if CONF.feature.storage == 'persistent':
            params.database.storage = farmrole.DataStorage()
        elif CONF.feature.storage == 'eph':
            params.database.storage = farmrole.DataStorage(engine='eph', type='ephemeral-disk-0')
        elif CONF.feature.storage == 'raid10':
            params.database.storage = farmrole.DataStorage(engine='raid', level=10, volumes=4)
        elif CONF.feature.storage == 'raid5':
            params.database.storage = farmrole.DataStorage(engine='raid', level=5, volumes=3)

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
            params.storage.volumes.append(
                farmrole.Volume(size=4, engine='eph', type='ephemeral0', fs='ntfs', mount='Z',
                                label='test_label', category='Ephemeral storage', re_use=False)
            )

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
    def set_winchef(params):
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.server = farmrole.ChefServer(
            url='https://api.opscode.com/organizations/webta')
        params.bootstrap_with_chef.runlist = '["recipe[windows_file_create::default]", "recipe[revizorenv]"]'

    @staticmethod
    def set_winchef_role(params):
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.server = farmrole.ChefServer(
            url='https://api.opscode.com/organizations/webta')
        params.bootstrap_with_chef.role_name = 'test_chef_role_windows'

    @staticmethod
    def set_chef_solo(params, options):
        chef_opts = options.split('-')
        if chef_opts[2] == 'private':
            url = 'git@github.com:Scalr/int-cookbooks.git'
            params.bootstrap_with_chef.path = 'cookbooks'
            params.bootstrap_with_chef.private_key = open(CONF.ssh.private_key, 'r').read()
        else:
            url = 'https://github.com/Scalr/sample-chef-repo.git'
        if chef_opts[-1] == 'branch':
            url = ''.join((url, '@revizor-test'))
        params.bootstrap_with_chef.enabled = True
        params.bootstrap_with_chef.cookbook_url = url
        params.bootstrap_with_chef.runlist = '["recipe[revizor-chef]"]'
        params.bootstrap_with_chef.attributes = '{"chef-solo":{"result":"%s"}}' % options.strip()
        params.bootstrap_with_chef.url_type = 'git'

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
        params.network.hostname_template = '{REVIZOR_FAILED_HOSTNAME}'

    @staticmethod
    def set_hostname(params):
        params.network.hostname_source = 'template'
        params.network.hostname_template = '{SCALR_FARM_ID}-{SCALR_FARM_ROLE_ID}-{SCALR_INSTANCE_INDEX}'

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
            farmrole.OrchestrationRule(event='HostUp', script='Sleep 10')
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
            farmrole.OrchestrationRule(event='HostUp', script='Windows ping-pong. CMD')
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
