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
             'test_szradm_listroles',
             'test_restart_scalarizr',
             'test_restart_scalarizr_script',
             'test_windows_reboot',
             'test_script_execution',
             'test_restart_farm',
             'test_reboot_bootstrap',
             'test_reboot_script',
             'test_failed_script',
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

    @pytest.mark.restart
    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_restart_scalarizr_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Restart scalarizr during script execution"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server,
                                  script_name='windows sleep 60',
                                  synchronous=True)
        windows.agent_restart(cloud, server)
        windows.validate_terminated_in_log(cloud, server)
        lib_node.validate_service(cloud, server, 'scalarizr')
        windows.validate_errors_in_log(cloud, server)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='windows sleep 60',
                                               new_only=True)

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

    @pytest.mark.scripting
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    @pytest.mark.parametrize('script_name, synchronous, is_local, output, stderr',
                             [
                                 ('Windows ping-pong. CMD', True, False, 'pong', None),
                                 ('Windows ping-pong. CMD', False, False, 'pong', None),
                                 ('Windows ping-pong. PS', True, False, 'pong', None),
                                 ('Windows ping-pong. PS', False, False, 'pong', None),
                                 ('Cross-platform script', False, False,
                                  'Multiplatform script successfully executed', None),
                                 ('https://gist.githubusercontent.com/gigimon/d233b77be7c04480c01a/raw'
                                  '/cd05c859209e1ff23961a371e0e2298ab3fb0257/gistfile1.txt', False, True,
                                  'Script runned from URL', None),
                                 ('https://gist.githubusercontent.com/Theramas/48753f91f4af72be12c03c0485b27f7d/raw'
                                  '/97caf55e74c8db6c5bf96b6a29e48c043ac873ed/test', False, True,
                                  'Multiplatform script successfully executed', None),
                                 ('Non ascii script wrong interpreter', False, False, None,
                                  "The only supported interpreters on Windows in first shebang are "
                                  "('powershell', 'cmd')"),
                                 ('Exit 1 with stdout message', False, False, 'Message in stdout section', None),
                                 ('Create local script', False, False, 'Directory: C:\; local_script.ps1', None),
                                 ('Non ascii script corect execution', False, False,
                                  'TUVWXyz; A?AA?AA?A-A?AA?AA?A', None),
                                 # ('C:\local_script.ps1', False, True, 'Local script work!', '')
                                 # ^ blocked by SCALARIZR-2470
                             ],
                             ids=[
                                 'ping-pong CMD blocking',
                                 'ping-pong CMD non-blocking',
                                 'ping-pong PS blocking',
                                 'ping-pong PS non-blocking',
                                 'cross-platform script',
                                 'from URL',
                                 'from URL multiplatform',
                                 'wrong interpreter',
                                 'exit 1 with stdout',
                                 'create local script',
                                 'non-ascii'
                             ])
    def test_script_execution(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                              script_name: str, synchronous: bool, is_local: bool, output: str, stderr: str):
        """Scripts executing on Windows"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name=script_name,
                                  synchronous=synchronous, is_local=is_local)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               log_contains=stderr if stderr else output,
                                               std_err=bool(stderr),
                                               new_only=True)

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
    def test_reboot_bootstrap(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Reboot on bootstraping"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['small_win_orchestration'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_hostname(server)

    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    @pytest.mark.parametrize('event, script_name, exitcode, output',
                             [
                                 ('HostInit', 'Windows_ping_pong_CMD', 0, 'pong'),
                                 ('HostUp', 'Windows_ping_pong_CMD', 0, 'pong')
                             ],
                             ids=[
                                 'HostInit',
                                 'HostUp'
                             ])
    def test_reboot_script(self, context: dict, cloud: Cloud, servers: dict,
                           event: str, script_name: str, exitcode: int, output: str):
        """Verify script execution on bootstrapping"""
        server = servers['M1']
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               event=event,
                                               log_contains=output,
                                               exitcode=exitcode)

    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_failed_script(self, context: dict, cloud: Cloud, farm: Farm):
        """Bootstrapping role with failed script"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_script'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.FAILED)
        lib_server.validate_failed_status_message(server,
                                                  phase='BeforeHostUp',
                                                  msg='execute.script\\bin\\Multiplatform_exit_1.ps1 exited with code 1')

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
