import pytest

from revizor2 import CONF
from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
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
             'test_hidden_variable',
             'test_restart_scalarizr',
             'test_custom_event',
             'test_custom_event_caching',
             'test_stop_farm',
             'test_delete_attached_storage',
             'test_start_farm',
             'test_attached_storages_restart',
             'test_reboot_bootstrap',
             'test_nonblank_volume',
             'test_failed_hostname')

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
        lifecycle.create_files(cloud, server, count=100, directory='/media/diskmount')
        if CONF.feature.platform == Platform.EC2:
            lifecycle.validate_path(cloud, server, '/media/partition')

    @pytest.mark.partition
    @pytest.mark.platform('ec2')
    def test_create_volume_snapshot(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Create volume snapshot"""
        server = servers['M1']
        lifecycle.create_partitions_on_volume(cloud, server, mnt_point='/media/partition')
        snapshot_id = lifecycle.create_volume_snapshot(context, farm, '/media/partition')
        context['volume_snapshot_id'] = snapshot_id
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
        mount_table = lifecycle.get_mount_table(cloud, server)
        context['M1_mount_table'] = mount_table
        lifecycle.validate_mount_point_in_fstab(cloud, server,
                                                mount_table=mount_table,
                                                mount_point='/media/diskmount')

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
                                               log_contains="Interpreter not found '/no/Ã§Ã£o'",
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
                                               log_contains='Ã¼',
                                               new_only=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='non-ascii-output',
                                               log_contains='クマ',
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

    @pytest.mark.restart
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_restart_scalarizr(self, cloud: Cloud, servers: dict):
        """Restart scalarizr"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_node.reboot_scalarizr(cloud, server)
        lib_node.validate_scalarizr_log_contains(cloud, server, message='Scalarizr terminated')
        lib_server.check_scalarizr_log_errors(cloud, server)

    @pytest.mark.event
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_custom_event(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Custom event"""
        server = servers['M1']
        event = lifecycle.define_event('TestEvent')
        lifecycle.attach_script(context, farm, event_name=event['name'], script_name='TestingEventScript')
        lib_node.execute_command(cloud, server, command='szradm --fire-event TestEvent file1=/tmp/f1 file2=/tmp/f2')
        lib_server.validate_server_message(cloud, farm, msgtype='out', msg='TestEvent', server=server)
        lifecycle.validate_path(cloud, server, path='/tmp/f1')
        lifecycle.validate_path(cloud, server, path='/tmp/f2')

    @pytest.mark.event
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_custom_event_caching(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Caching custom event parameters"""
        server = servers['M1']
        event = lifecycle.define_event('TestEvent')
        lifecycle.attach_script(context, farm, event_name=event['name'], script_name='TestingEventScript')
        lib_node.execute_command(cloud, server,
                                 command='szradm --fire-event TestEvent file1=/tmp/nocache1 file2=/tmp/nocache2')
        lib_server.validate_server_message(cloud, farm, msgtype='out', msg='TestEvent', server=server)
        lifecycle.validate_path(cloud, server, path='/tmp/nocache1')
        lifecycle.validate_path(cloud, server, path='/tmp/nocache2')

    @pytest.mark.restartfarm
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_stop_farm(self, farm: Farm):
        """Stop farm"""
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')

    @pytest.mark.storages
    @pytest.mark.platform('ec2', 'gce', 'cloudstack')
    def test_delete_attached_storage(self, context: dict, cloud: Cloud, farm: Farm):
        """Delete attached storage"""
        device_id = lifecycle.get_device_for_additional_storage(context, farm, mount_point='/media/diskmount')
        context['M1_device_media_diskmount'] = device_id
        lifecycle.delete_volume(cloud, device_id)

    @pytest.mark.restartfarm
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_start_farm(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Start farm"""
        lib_farm.farm_launch_delayed(farm)
        server = lib_server.expect_server_bootstraping_for_role(context, cloud, farm)
        servers['M1'] = server
        lib_node.validate_scalarizr_version(server, 'system')

    @pytest.mark.storages
    @pytest.mark.platform('ec2', 'cloudstack', 'gce')
    def test_attached_storages_restart(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check attached storages after farm restart"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        old_details = context['M1_hostup_volumes']
        lifecycle.validate_message_config(cloud, server,
                                          config_group='volumes', message='HostInitResponse',
                                          old_details=old_details)
        lifecycle.validate_path(cloud, server, '/media/diskmount')
        device_id = context['M1_device_media_diskmount']
        lifecycle.validate_device_changed(context, farm, mount_point='/media/diskmount', old_device_id=device_id)

    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure')
    def test_reboot_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Reboot on bootstraping"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['init_reboot', 'small_linux_orchestration'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Revizor last reboot',
                                               event='HostInit',
                                               user='root',
                                               exitcode=0)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Revizor last reboot',
                                               event='HostUp',
                                               user='root',
                                               exitcode=0)
        lifecycle.validate_scripts_launch_amt(server, 'Revizor last reboot')
        lifecycle.validate_hostname(server)

    @pytest.mark.partition
    @pytest.mark.platform('ec2')
    def test_nonblank_volume(self, context: dict, cloud: Cloud, farm: Farm):
        """Check partition table recognized as a non-blank volume"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        snapshot_id = context['volume_snapshot_id']
        lifecycle.add_storage_to_role(context, farm, snapshot_id)
        farm.launch()
        lib_server.wait_status(context, cloud, farm, status=ServerStatus.FAILED)

    @pytest.mark.failedbootstrap
    @pytest.mark.platform('ec2', 'vmware', 'gce', 'cloudstack', 'openstack')
    def test_failed_hostname(self, context: dict, cloud: Cloud, farm: Farm):
        """Failed bootstrap by hostname"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_hostname'])
        farm.launch()
        lib_server.wait_status(context, cloud, farm, status=ServerStatus.FAILED)
