import pytest

from revizor2 import CONF
from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform, FarmStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, provision


class TestStopResume:
    """Test stop/resume server with attached disks and stop/resume farm"""
    order = (
        'test_bootstrapping',
        'test_chef_deployment_linux',
        'test_chef_deployment_windows',
        'test_stop_resume',
        'test_chef_after_resume_linux',
        'test_chef_after_resume_windows',
        'test_attached_storages_after_resume',
        'test_farm_stop_resume'
    )

    @pytest.mark.farm_resume
    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'])
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        options = ['storages', 'chef', 'termination_preferences']
        if CONF.feature.dist.is_windows:
            options = ['winchef', 'termination_preferences']
        lib_farm.add_role_to_farm(context, farm, role_options=options)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_szr_version_last(server)

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'], family=['!windows'])
    def test_chef_deployment_linux(self, context: dict, cloud: Cloud, servers: dict):
        """Verify chef executed fine"""
        server = servers['M1']
        node = cloud.get_node(server)
        context['chef_deployment_time'] = provision.get_chef_bootstrap_stat(node)
        provision.check_process_options(node, 'memcached', '-m 1024')
        provision.check_process_options(node, 'chef-client', '--daemonize')
        provision.verify_chef_hostname(cloud, server)

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'], family=['windows'])
    def test_chef_deployment_windows(self, context: dict, cloud: Cloud, servers: dict):
        """Verify chef executed fine"""
        node = cloud.get_node(servers['M1'])
        provision.check_file_exist_on_win(node, 'C:\\chef_result_file')
        provision.remove_file_on_win(node, 'C:\\chef_result_file')

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'])
    def test_stop_resume(self, context: dict, cloud: Cloud, servers: dict, farm: Farm):
        """Verify server stop/resume work"""
        server = servers['M1']
        lib_server.execute_server_action(server, 'suspend')
        lib_server.assert_server_event(server, ['BeforeHostTerminate (Suspend)'])
        lib_server.assert_server_message(cloud, farm, msgtype='out', msg='BeforeHostTerminate', server=server)
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.SUSPENDED)
        lib_server.assert_server_event(server, ['HostDown (Suspend)'])
        provision.check_node_exists_on_chef_server(server)
        servers['M2'] = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lib_server.execute_server_action(server, 'resume')
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RESUMING)
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        lib_server.assert_server_event(server, ['ResumeComplete'])
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RUNNING)
        lib_server.assert_server_event_again_fired(server, ['HostInit', 'BeforeHostUp'])

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'], family=['!windows'])
    def test_chef_after_resume_linux(self, context: dict, cloud: Cloud, servers: dict, farm: Farm):
        """Verify chef not executed after resume"""
        server = servers['M1']
        node = cloud.get_node(server)
        assert context['chef_deployment_time'] == provision.get_chef_bootstrap_stat(node), \
            'Chef was started after resume!'
        provision.check_process_status(node, 'memcached', False)
        provision.check_process_options(node, 'chef-client', '--daemonize')
        provision.verify_chef_hostname(cloud, server)

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'], family=['windows'])
    def test_chef_after_resume_windows(self, context: dict, cloud: Cloud, servers: dict, farm: Farm):
        """Verify chef not executed after resume"""
        node = cloud.get_node(servers['M1'])
        provision.check_file_exist_on_win(node, 'C:\\chef_result_file', exist=False)

    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'], family=['!windows'])
    def test_attached_storages_after_resume(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check attached storages after resume"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lifecycle.assert_attached_disk_types(context, cloud, farm)
        lifecycle.assert_path_exist(cloud, server, '/media/diskmount')
        if CONF.feature.platform in [Platform.EC2, Platform.AZURE]:
            lifecycle.assert_path_exist(cloud, server, '/media/partition')

        mount_table = lifecycle.get_mount_table(cloud, server)
        lifecycle.assert_mount_point_in_fstab(cloud, server,
                                              mount_table=mount_table,
                                              mount_point='/media/diskmount')

    @pytest.mark.farm_resume
    @pytest.mark.run_only_if(platform=['ec2', 'gce', 'openstack', 'azure'])
    def test_farm_stop_resume(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Farm suspend test"""
        farm.servers.reload()
        farm.suspend()
        provision.wait_for_farm_state(farm, FarmStatus.SUSPENDED)
        for server in farm.servers:
            lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.SUSPENDED)
        farm.resume()
        for server in farm.servers:
            lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RESUMING)
        for server in farm.servers:
            lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
            lib_server.assert_server_event(server, ['ResumeComplete'])
        for server in farm.servers:
            lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RUNNING)
