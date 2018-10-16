import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, szradm


class TestLifecycleLinux:
    """
    Linux server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes
    """

    order = ('test_bootstrapping',
             'test_szradm_listroles',
             'test_attached_storages',
             'test_create_volume_snapshot',
             'test_storages_fstab',
             'test_linux_reboot',
             'test_storages_fstab_reboot',
             'test_execute_script',
             'test_execute_nonascii_script',
             'test_execute_nonascii_script_wrong',
             'test_nonascii_script_out',
             'test_hidden_variable')

    @pytest.mark.boot
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['storages', 'noiptables'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_vcpus_info(server)
        lifecycle.validate_scalarizr_version(server)
        lifecycle.validate_hostname(server)
        lifecycle.validate_iptables_ports(cloud, server, [8008, 8010, 8012, 8013, 8014], invert=True)
        lifecycle.validate_server_message_count(context, server, 'BlockDeviceMounted')

    @pytest.mark.szradm
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_szradm_listroles(self, cloud: Cloud, servers: dict):
        """Verify szradm list-roles"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        szradm.validate_external_ip(cloud, server)
        szradm.validate_key_records(cloud, server,
                                    command='szradm --queryenv get-latest-version',
                                    key='version',
                                    count=1)
        szradm.validate_key_records(cloud, server,
                                    command='szradm list-messages',
                                    key='name',
                                    record='HostUp')

    @pytest.mark.storages
    @pytest.mark.platform('ec2', 'cloudstack', 'gce', 'azure')
    def test_attached_storages(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check attached storages"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        context['M1_hostup_volumes'] = lifecycle.get_config_from_message(cloud,
                                                                         server,
                                                                         config_group='volumes',
                                                                         message='HostUp')
        lifecycle.validate_attached_disk_types(context, cloud, farm)
        lifecycle.validate_path(cloud, server, '/media/diskmount')
        lifecycle.validate_path(cloud, server, '/media/raidmount')
        lifecycle.validate_path(cloud, server, '/media/partition')
        lifecycle.create_files(cloud, server, count=100, directory='/media/diskmount')
        lifecycle.create_files(cloud, server, count=100, directory='/media/raidmount')

    @pytest.mark.partition
    @pytest.mark.platform('ec2')
    def test_create_volume_snapshot(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Create volume snapshot"""
        server = servers['M1']
        lifecycle.create_partitions_on_volume(cloud, server, mnt_point='/media/partition')
        snapshot_id = lifecycle.create_volume_snapshot(context, farm, '/media/partition')
        lifecycle.validate_volume_snapshot(snapshot_id)

    @pytest.mark.fstab
    @pytest.mark.storages
    @pytest.mark.platform('ec2', 'cloudstack', 'gce', 'azure')
    def test_storages_fstab(self, context: dict, cloud: Cloud, servers: dict):
        """Verify attached storages in fstab"""
        server = servers['M1']
        mount_table = lifecycle.get_mount_table(cloud, server)
        context['M1_mount_table'] = mount_table
        lifecycle.validate_mount_point_in_fstab(cloud, server,
                                                mount_table=mount_table,
                                                mount_point='/media/diskmount')
        lifecycle.validate_mount_point_in_fstab(cloud, server,
                                                mount_table=mount_table,
                                                mount_point='/media/raidmount')

    @pytest.mark.reboot
    @pytest.mark.platform('ec2', 'vmware', 'cloudstack', 'gce', 'rackspaceng', 'azure')
    def test_linux_reboot(self, cloud: Cloud, farm: Farm, servers: dict):
        """Linux reboot"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)

    @pytest.mark.fstab
    @pytest.mark.storages
    @pytest.mark.platform('ec2', 'cloudstack', 'azure')
    def test_storages_fstab_reboot(self, context: dict, cloud: Cloud, servers: dict):
        """Verify attached storages in fstab after reboot"""
        server = servers['M1']
        mount_table = context['M1_mount_table']
        lifecycle.validate_mount_point_in_fstab(cloud, server,
                                                mount_table=mount_table,
                                                mount_point='/media/diskmount')
        lifecycle.validate_mount_point_in_fstab(cloud, server,
                                                mount_table=mount_table,
                                                mount_point='/media/raidmount')

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_execute_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Execute script on Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_execute_nonascii_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Execute non-ascii script on Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='Non ascii script', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Non ascii script',
                                               log_contains='Non_ascii_script',
                                               new_only=True)

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_execute_nonascii_script_wrong(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Execute non-ascii script with wrong interpreter on Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server,
                                  script_name='Non ascii script wrong interpreter', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Non ascii script wrong interpreter',
                                               log_contains="Interpreter not found '/no/ÃƒÂ§ÃƒÂ£o'",
                                               std_err=True, new_only=True)

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_nonascii_script_out(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check non-ascii script output on Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server,
                                  script_name='non-ascii-output', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='non-ascii-output',
                                               log_contains='ÃƒÂ¼',
                                               new_only=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='non-ascii-output',
                                               log_contains='ã‚¯ãƒž',
                                               std_err=True, new_only=True)

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_hidden_variable(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Verify hidden global variable"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.validate_string_in_file(cloud, server, file_path='/etc/profile.d/scalr_globals.sh',
                                           value='revizor_hidden_var', invert=True)
        lib_server.execute_script(context, farm, server,
                                  script_name='Verify hidden variable', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Verify hidden variable',
                                               log_contains='REVIZOR_HIDDEN_VARIABLE',
                                               new_only=True)
