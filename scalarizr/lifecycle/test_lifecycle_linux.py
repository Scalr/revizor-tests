import json
import time
import pytest
import logging

from random import randint
from _pytest.fixtures import FixtureRequest

from revizor2 import CONF
from revizor2.cloud import Cloud
from revizor2.api import Farm, Role
from revizor2.consts import ServerStatus, Platform

from scalarizr.lib import scalr
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, szradm, rebundle
from scalarizr.lib import cloud_resources as lib_resources

LOG = logging.getLogger(__name__)


@pytest.fixture
def efs(request: FixtureRequest, farm: Farm) -> dict:
    platform = CONF.feature.platform
    user = scalr.get_scalr_user_by_email_local_part("test")
    # New efs
    LOG.info('Create new Amazon elastic file system')
    efs = lib_resources.efs_create(
        f"revizor-{randint(9000, 9999)}",
        platform.location,
        platform.vpc_id,
        user[0]['id']
    )
    # Add mount target to efs
    mount_target = lib_resources.create_efs_mount_target(
        efs['fileSystemId'],
        platform.vpc_id,
        json.loads(platform.vpc_subnet_id)[0],
        platform.zone,
        platform.location)
    LOG.debug(f'Added new EFS [{efs["fileSystemId"]}] with mounts target [{mount_target}].')
    yield efs
    # Remove from cloud linked to farm resources
    if not request.session.config.getoption("--no-stop-farm"):
        lib_farm.remove_cloud_resources_linked_to_farm(farm)


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
             'test_execute_git_script',
             'test_restart_scalarizr',
             'test_custom_event',
             'test_custom_event_caching',
             'test_stop_farm',
             'test_delete_attached_storage',
             'test_start_farm',
             'test_attached_storages_restart',
             'test_reboot_bootstrap',
             'test_nonblank_volume',
             'test_failed_hostname',
             'test_efs_bootstrapping',
             'test_attach_disk_to_running_server',
             'test_server_rebundle',
             'test_bootstrapping_auto_placement_strategy'
             )

    @pytest.mark.boot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['storages', 'noiptables'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_vcpu_count(server)
        lifecycle.assert_szr_version_last(server)
        lifecycle.assert_hostname(server)
        lifecycle.assert_iptables_ports_status(cloud, server, [8008, 8010, 8012, 8013, 8014], invert=True)
        lifecycle.assert_server_message_count(context, server, 'BlockDeviceMounted')
        lib_server.assert_scalarizr_log_errors(cloud, server)

    @pytest.mark.szradm
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_szradm_listroles(self, cloud: Cloud, servers: dict):
        """Verify szradm list-roles"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        szradm.assert_szradm_public_ip(cloud, server)
        szradm.assert_szradm_records_count(cloud, server,
                                           command='szradm --queryenv get-latest-version',
                                           key='version',
                                           count=1)
        szradm.assert_szradm_records_count(cloud, server,
                                           command='szradm list-messages',
                                           key='name',
                                           record='HostUp')

    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.AZURE, Platform.VMWARE])
    def test_attached_storages(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check attached storages"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        context['M1_hostup_volumes'] = lifecycle.get_config_from_message(cloud,
                                                                         server,
                                                                         config_group='volumes',
                                                                         message='HostInitResponse')
        if CONF.feature.platform.is_gce:
            lifecycle.assert_attached_disk_types(context, cloud, farm)
        lifecycle.assert_path_exist(cloud, server, '/media/diskmount')
        lifecycle.create_files(cloud, server, count=100, directory='/media/diskmount')
        if CONF.feature.platform in [Platform.EC2, Platform.AZURE]:
            lifecycle.assert_path_exist(cloud, server, '/media/partition')
        lifecycle.assert_file_count(cloud, server, count=100, directory='/media/diskmount')

    @pytest.mark.partition
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.AZURE])
    def test_create_volume_snapshot(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Create volume snapshot"""
        server = servers['M1']
        mnt_point = '/media/partition'
        lifecycle.create_partitions_on_volume(cloud, server, mnt_point=mnt_point)
        snapshot_id = lifecycle.create_volume_snapshot(context, farm, mnt_point=mnt_point)
        context['volume_snapshot_id'] = snapshot_id
        lifecycle.assert_volume_snapshot_created(snapshot_id)

    @pytest.mark.fstab
    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.AZURE, Platform.VMWARE])
    def test_storages_fstab(self, context: dict, cloud: Cloud, servers: dict):
        """Verify attached storages in fstab"""
        server = servers['M1']
        mount_table = lifecycle.get_mount_table(cloud, server)
        context['M1_mount_table'] = mount_table
        lifecycle.assert_mount_point_in_fstab(cloud, server,
                                              mount_table=mount_table,
                                              mount_point='/media/diskmount')

    @pytest.mark.reboot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_linux_reboot(self, cloud: Cloud, farm: Farm, servers: dict):
        """Linux reboot"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_server_action(server, 'reboot')
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)

    @pytest.mark.fstab
    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.AZURE, Platform.VMWARE])
    def test_storages_fstab_reboot(self, context: dict, cloud: Cloud, servers: dict):
        """Verify attached storages in fstab after reboot"""
        server = servers['M1']
        mount_table = lifecycle.get_mount_table(cloud, server)
        context['M1_mount_table'] = mount_table
        lifecycle.assert_mount_point_in_fstab(cloud, server,
                                              mount_table=mount_table,
                                              mount_point='/media/diskmount')
        lifecycle.assert_file_count(cloud, server, count=100, directory='/media/diskmount')

    @pytest.mark.scripting
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_execute_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Execute script on Linux"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Linux ping-pong',
                                             log_contains='pong',
                                             new_only=True)

    @pytest.mark.scripting
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_execute_git_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Execute Git script on Linux"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='Git_scripting_lifecycle', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Git_scripting_lifecycle',
                                             log_contains='Multiplatform script successfully executed')

    @pytest.mark.restart
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_restart_scalarizr(self, cloud: Cloud, servers: dict):
        """Restart scalarizr"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_node.reboot_scalarizr(cloud, server)
        lib_node.assert_scalarizr_log_contains(cloud, server, message='Scalarizr terminated')
        lib_server.assert_scalarizr_log_errors(cloud, server)

    @pytest.mark.event
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_custom_event(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Custom event"""
        server = servers['M1']
        event = lifecycle.define_event('TestEvent')
        lifecycle.attach_script(context, farm, event_name=event['name'], script_name='TestingEventScript')
        lib_node.execute_command(cloud, server, command='szradm --fire-event TestEvent file1=/tmp/f1 file2=/tmp/f2')
        lib_server.assert_server_message(cloud, farm, msgtype='out', msg='TestEvent', server=server)
        lifecycle.assert_path_exist(cloud, server, path='/tmp/f1')
        lifecycle.assert_path_exist(cloud, server, path='/tmp/f2')

    @pytest.mark.event
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_custom_event_caching(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Caching custom event parameters"""
        server = servers['M1']
        event = lifecycle.define_event('TestEvent')
        lifecycle.attach_script(context, farm, event_name=event['name'], script_name='TestingEventScript')
        lib_node.execute_command(cloud, server,
                                 command='szradm --fire-event TestEvent file1=/tmp/nocache1 file2=/tmp/nocache2')
        lib_server.assert_server_message(cloud, farm, msgtype='out', msg='TestEvent', server=server)
        lifecycle.assert_path_exist(cloud, server, path='/tmp/nocache1')
        lifecycle.assert_path_exist(cloud, server, path='/tmp/nocache2')

    @pytest.mark.restartfarm
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_stop_farm(self, farm: Farm):
        """Stop farm"""
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')

    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE])
    def test_delete_attached_storage(self, context: dict, cloud: Cloud, farm: Farm):
        """Delete attached storage"""
        device_id = lifecycle.get_device_for_additional_storage(context, farm, mount_point='/media/diskmount')
        context['M1_device_media_diskmount'] = device_id
        lifecycle.delete_volume(cloud, device_id)

    @pytest.mark.restartfarm
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_start_farm(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Start farm"""
        if CONF.feature.platform.is_cloudstack:
            time.sleep(1800)
        farm.launch()
        server = lib_server.expect_server_bootstraping_for_role(context, cloud, farm)
        servers['M1'] = server
        lib_node.assert_scalarizr_version(server, 'system')

    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE])
    def test_attached_storages_restart(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check attached storages after farm restart"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        old_details = context['M1_hostup_volumes']
        lifecycle.assert_server_message_body(cloud, server,
                                             config_group='volumes', message='HostInitResponse',
                                             old_details=old_details)
        lifecycle.assert_path_exist(cloud, server, '/media/diskmount')
        device_id = context['M1_device_media_diskmount']
        lifecycle.assert_volume_device_changed(context, farm, mount_point='/media/diskmount', old_device_id=device_id)

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_reboot_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Reboot on bootstraping"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['init_reboot', 'small_linux_orchestration'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Revizor last reboot',
                                             event='HostInit',
                                             user='root',
                                             exitcode=0)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Revizor last reboot',
                                             event='HostUp',
                                             user='root',
                                             exitcode=0)
        lifecycle.validate_scripts_launch_amt(server, 'Revizor last reboot')
        lifecycle.assert_hostname(server)

    @pytest.mark.partition
    @pytest.mark.run_only_if(platform=[Platform.EC2])
    def test_nonblank_volume(self, context: dict, cloud: Cloud, farm: Farm):
        """Check partition table recognized as a non-blank volume"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        snapshot_id = context['volume_snapshot_id']
        lifecycle.add_storage_to_role(context, farm, snapshot_id)
        farm.launch()
        lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.FAILED)

    @pytest.mark.failedbootstrap
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK])
    def test_failed_hostname(self, context: dict, cloud: Cloud, farm: Farm):
        """Failed bootstrap by hostname"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_hostname'])
        farm.launch()
        lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.FAILED)

    @pytest.mark.efs
    @pytest.mark.storages
    @pytest.mark.run_only_if(platform=[Platform.EC2])
    def test_efs_bootstrapping(self, efs: dict, context: dict, farm: Farm, cloud: Cloud):
        """Attach EFS storage"""
        lib_farm.clear(farm)
        farm.terminate()
        context['linked_services'] = {'efs': {'cloud_id': efs['fileSystemId']}}
        efs_mount_point = "/media/efsmount"
        lib_farm.link_efs_cloud_service_to_farm(farm, efs)
        lib_farm.add_role_to_farm(context, farm, role_options=['efs'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.assert_attached_disk_types(context, cloud, farm)
        lifecycle.assert_path_exist(cloud, server, efs_mount_point)
        lifecycle.create_files(cloud, server, count=100, directory=efs_mount_point)
        mount_table = lifecycle.get_mount_table(cloud, server)
        lifecycle.assert_mount_point_in_fstab(
            cloud,
            server,
            mount_table=mount_table,
            mount_point=efs_mount_point)
        # Reboot server
        lib_server.execute_server_action(server, 'reboot')
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        # Check after reboot
        lifecycle.assert_attached_disk_types(context, cloud, farm)
        lifecycle.assert_path_exist(cloud, server, efs_mount_point)
        lifecycle.assert_file_count(cloud, server, count=100, directory=efs_mount_point)

    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_attach_disk_to_running_server(self, context: dict, cloud: Cloud, farm: Farm):
        """Attach disk to running server"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        volume_id = lifecycle.create_and_attach_volume(server, size=1)
        assert volume_id, f'New volume for server {server.id} not created!'
        for _ in range(6):
            server.details.reload()
            volume_ids = [vol['id'] for vol in server.details['volumes']]
            if len(volume_ids) > 1:
                break
            time.sleep(5)
        else:
            raise AssertionError(f'Servers {server.id} has only 1 volume after 30 seconds')
        assert volume_id in volume_ids, f'Server {server.id} not have volume {volume_id}'

    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.OPENSTACK, Platform.AZURE, Platform.GCE, Platform.VMWARE])
    def test_server_rebundle(self, context: dict, cloud: Cloud, farm: Farm):
        """Verify server rebundle work"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        bundle_id = rebundle.start_server_rebundle(server)
        rebundle.assert_bundle_task_created(server, bundle_id)
        new_role_id = rebundle.wait_bundle_complete(server, bundle_id)
        farm.clear_roles()
        lib_farm.add_role_to_farm(context, farm, role=Role.get(new_role_id))
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.assert_szr_version_last(server)
        lib_server.assert_scalarizr_log_errors(cloud, server)

    @pytest.mark.run_only_if(platform=[Platform.VMWARE])
    def test_bootstrapping_auto_placement_strategy(self, context: dict, cloud: Cloud, farm: Farm):
        """Verify server bootstrapping with scalr auto placement strategy"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['scalr-auto'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.assert_szr_version_last(server)
        lib_server.assert_scalarizr_log_errors(cloud, server)
