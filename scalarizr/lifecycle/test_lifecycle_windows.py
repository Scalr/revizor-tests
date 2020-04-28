import time
import pytest

from revizor2.conf import CONF
from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, szradm, windows


class TestLifecycleWindows:
    """
    Windows server lifecycle
    In order to manage server lifecycle
    As a scalr user
    I want to be able to monitor server state changes
    """

    order = ('test_bootstrapping',
             'test_execute_script',
             'test_execute_git_script',
             'test_szradm_listroles',
             'test_restart_scalarizr',
             'test_windows_reboot',
             'test_restart_farm',
             'test_restart_bootstrap',
             # 'test_eph_bootstrap',
             'test_attach_disk_to_running_server')

    @pytest.mark.boot
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['storages'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_vcpu_count(server)
        if CONF.feature.platform in [Platform.EC2, Platform.GCE, Platform.AZURE, Platform.VMWARE]:
            windows.assert_attached_disks_size(cloud, server, [
                ('E:\\', 'test_label', 1),
                ('F:\\', '', 2),
                ('C:\\diskmount\\', '', 3)
            ])
        lifecycle.assert_szr_version_last(server)
        lifecycle.assert_hostname(server)

    @pytest.mark.scripting
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_execute_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Basic script execution"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name="Windows ping-pong. CMD",
                                  synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)

    @pytest.mark.scripting
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_execute_git_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Git script execution on windows"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name="Git_scripting_lifecycle",
                                  synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Git_scripting_lifecycle',
                                             log_contains='Multiplatform script successfully executed')

    @pytest.mark.szradm
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
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

    @pytest.mark.restart
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_restart_scalarizr(self, cloud: Cloud, servers: dict):
        """Restart scalarizr"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        windows.agent_restart(cloud, server)
        windows.assert_szr_terminated_in_log(cloud, server)
        lib_node.assert_service_work(cloud, server, 'scalarizr')
        windows.assert_errors_in_szr_logs(cloud, server)

    @pytest.mark.reboot
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_windows_reboot(self, cloud: Cloud, farm: Farm, servers: dict):
        """Windows reboot"""
        server = servers['M1']
        lib_server.execute_server_action(server, 'reboot')
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='Win_HostDown', server=server)
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        lib_server.assert_server_message(cloud, farm, msgtype='out', msg='RebootFinish', server=server)
        lib_node.assert_service_work(cloud, server, 'scalarizr')
        lib_node.assert_service_work(cloud, server, 'scalr-upd-client')

    @pytest.mark.restartfarm
    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_restart_farm(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Restart farm"""
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')
        farm.launch()
        server = lib_server.expect_server_bootstraping_for_role(context, cloud, farm)
        servers['M1'] = server
        lifecycle.assert_hostname(server)

    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.GCE, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_restart_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstraping on restart"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_hostname(server)

    # @pytest.mark.run_only_if(platform=[Platform.EC2])
    # def test_eph_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
    #     """Bootstraping with ephemeral"""
    #     lib_farm.clear(farm)
    #     farm.terminate()
    #     lib_farm.add_role_to_farm(context, farm, role_options=['ephemeral'])
    #     farm.launch()
    #     server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
    #     servers['M1'] = server
    #     lifecycle.assert_vcpu_count(server)
    #     windows.assert_attached_disks_size(cloud, server, [('Z:\\', 'test_label', 4)])
    #     lifecycle.assert_szr_version_last(server)

    @pytest.mark.run_only_if(platform=[Platform.EC2, Platform.OPENSTACK, Platform.AZURE, Platform.VMWARE])
    def test_attach_disk_to_running_server(self, context: dict, cloud: Cloud, farm: Farm):
        """Attach disk to running server"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        volume_id = lifecycle.create_and_attach_volume(server, size=1)
        assert volume_id
        for _ in range(6):
            server.details.reload()
            volume_ids = [vol['id'] for vol in server.details['volumes']]
            if len(volume_ids) > 1:
                break
            time.sleep(5)
        else:
            raise AssertionError(f'Servers {server.id} has only 1 volume after 30 seconds')
        assert volume_id in volume_ids, f'Server {server.id} not have volume {volume_id}'
