import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
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
             'test_szradm_listroles',
             'test_restart_scalarizr',
             'test_windows_reboot',
             'test_restart_farm',
             'test_restart_bootstrap',
             'test_eph_bootstrap')

    @pytest.mark.boot
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['storages'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_vcpus_info(server)
        windows.validate_attached_disk_size(cloud, server, [
            ('E:\\', 'test_label', 1),
            ('F:\\', '', 2),
            ('C:\\diskmount\\', '', 3)
        ])
        lifecycle.validate_scalarizr_version(server)
        lifecycle.validate_hostname(server)

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_execute_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Basic script execution"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name="Windows ping-pong. CMD",
                                  synchronous=True, is_local=False)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Windows ping-pong. CMD',
                                               log_contains='pong',
                                               new_only=True)

    @pytest.mark.szradm
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
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

    @pytest.mark.restart
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_restart_scalarizr(self, cloud: Cloud, servers: dict):
        """Restart scalarizr"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        windows.agent_restart(cloud, server)
        windows.validate_terminated_in_log(cloud, server)
        lib_node.validate_service(cloud, server, 'scalarizr')
        windows.validate_errors_in_log(cloud, server)

    @pytest.mark.reboot
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_windows_reboot(self, cloud: Cloud, farm: Farm, servers: dict):
        """Windows reboot"""
        server = servers['M1']
        lib_server.execute_state_action(server, 'reboot')
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg='Win_HostDown', server=server)
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        lib_server.validate_server_message(cloud, farm, msgtype='out', msg='RebootFinish', server=server)
        lib_node.validate_service(cloud, server, 'scalarizr')
        lib_node.validate_service(cloud, server, 'scalr-upd-client')

    @pytest.mark.restartfarm
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_restart_farm(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Restart farm"""
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')
        farm.launch()
        server = lib_server.expect_server_bootstraping_for_role(context, cloud, farm)
        servers['M1'] = server
        lifecycle.validate_hostname(server)

    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_restart_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstraping on restart"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_hostname(server)

    @pytest.mark.platform('ec2')
    def test_eph_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstraping with ephemeral"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['ephemeral'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_vcpus_info(server)
        windows.validate_attached_disk_size(cloud, server, [('Z:\\', 'test_label', 4)])
        lifecycle.validate_scalarizr_version(server)
