import pytest

from revizor2.api import Farm, CONF
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, windows


WINDOWS_BOOTSTRAP_SCRIPTS = [
    ("HostInit", "Windows_ping_pong_CMD", None, 0, "pong", False),
    ("HostUp", "Windows_ping_pong_CMD", None, 0, "pong", False),
    ("HostUp", "Git_scripting_orchestration", None, 0, "Multiplatform script successfully executed", False)]

LINUX_BOOTSTRAP_SCRIPTS = [
    ("HostInit", "Revizor orchestration init", "root", 0, "", False),
    ("HostInit", "/tmp/script.sh", "root", 1, "", False),
    ("HostInit", "https://gist.githubusercontent.com", "root", 0, "Script runned from URL", False),
    ("BeforeHostUp", "Linux ping-pong", "root", 0, "pong", False),
    ("BeforeHostUp", "chef", "root", 0, '"HOME"=>"/root";"USER"=>"root"', False),
    ("HostUp", "Linux ping-pong", "revizor2", 1, "", "STDERR: no such user: 'revizor2'"),
    ("HostUp", "/home/revizor/local_script.sh", "revizor", 0, "Local script work! User: revizor; USER=revizor; HOME=/home/revizor", False),
    ("HostUp", "Linux ping-pong", "revizor", 0, "pong", False),
    ("HostUp", "chef", "root", 0, "", False),
    ("HostUp", "/bin/uname", "root", 0, "Linux", False),
    ("HostUp", "https://gist.githubusercontent.com", "root", 0, "Multiplatform script successfully executed", False),
    ("HostUp", "Sleep 10", "root", 130, "printing dot each second; .....", False),
    ("HostUp", "Git_scripting_orchestration", "root", 0, "Multiplatform script successfully executed", False)]

WINDOWS_SCRIPTS = [
    ('Windows ping-pong. CMD', True, False, 'pong', False),
    ('Windows ping-pong. CMD', False, False, 'pong', False),
    ('Windows ping-pong. PS', True, False, 'pong', False),
    ('Windows ping-pong. PS', False, False, 'pong', False),
    ('Cross-platform script', False, False,
     'Multiplatform script successfully executed', False),
    ('https://gist.githubusercontent.com/gigimon/d233b77be7c04480c01a/raw'
     '/cd05c859209e1ff23961a371e0e2298ab3fb0257/gistfile1.txt', False, True, 'Script runned from URL', False),
    ('https://gist.githubusercontent.com/Theramas/48753f91f4af72be12c03c0485b27f7d/raw'
     '/97caf55e74c8db6c5bf96b6a29e48c043ac873ed/test', False, True, 'Multiplatform script successfully executed', False),
    ('Non ascii script wrong interpreter', False, False,
     "The only supported interpreters on Windows in first shebang are ('powershell', 'cmd', 'cscript')", True),
    ('Exit 1 with stdout message', False, False, 'Message in stdout section', False),
    ('Create local script', False, False, r'Directory: C:\; local_script.ps1', False),
    ('Non ascii script corect execution', False, False,
     'abcdefg     HIJKLMNOP     qrs     TUVWXyz', False),
    # ('C:\local_script.ps1', False, True, 'Local script work!', '')
    # ^ blocked by SCALARIZR-2470
]

LINUX_SCRIPTS = [
    ("Linux ping-pong", False, False, "pong", False),
    ("Linux ping-pong", True, False, "pong", False),
    ("/home/revizor/local_script.sh", True, True,
     "Local script work!; USER=root; HOME=/root", False),
    ("/home/revizor/local_script.sh", False, True,
     "Local script work!; USER=root; HOME=/root", False),
    ("https://gist.githubusercontent.com/Theramas/5b2a9788df316606f72883ab1c3770cc/raw"
     "/3ae1a3f311d8e43053fbd841e8d0f17daf1d5d66/multiplatform", False, True,
     "Multiplatform script successfully executed", False),
    ("Cross-platform script", False, False,
     "Multiplatform script successfully executed", False),
    ("Non ascii script", True, False, "Non_ascii_script", False),
    ("Non ascii script wrong interpreter", True, False, "Interpreter not found '/no/Ã§Ã£o'", True),
    ("non-ascii-output", True, False, "Ã¼", False),
    ("Verify hidden variable", True, False, "REVIZOR_HIDDEN_VARIABLE", False)
]


def pytest_generate_tests(metafunc):
    if metafunc.function.__name__ == "test_verify_script_execution_on_bootstrap":
        if CONF.feature.dist.is_windows:
            metafunc.parametrize(
                "event, script_name, user, exitcode, output, stderr",
                WINDOWS_BOOTSTRAP_SCRIPTS)
        else:
            metafunc.parametrize(
                "event, script_name, user, exitcode, output, stderr",
                LINUX_BOOTSTRAP_SCRIPTS)
    elif metafunc.function.__name__ == "test_execute_scripts":
        if CONF.feature.dist.is_windows:
            metafunc.parametrize(
                "script_name, synchronous, is_local, output, stderr",
                WINDOWS_SCRIPTS)
        else:
            metafunc.parametrize(
                "script_name, synchronous, is_local, output, stderr",
                LINUX_SCRIPTS)


class TestOrchestration:
    """
    Linux orchestration feature test
    """

    order = ('test_bootstrapping',
             'test_verify_script_execution_on_bootstrap',
             'test_verify_chef_execution',
             'test_execute_scripts',
             'test_execute_scripts_user',
             'test_restart_scalarizr_script',
             'test_bootstrap_with_fail_script',
             'test_scripting_gv_length')

    @pytest.mark.boot
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        if CONF.feature.dist.is_windows:
            lib_farm.add_role_to_farm(context, farm, role_options=['small_win_orchestration'])
        else:
            lib_farm.add_role_to_farm(context, farm, role_options=['orchestration', 'chef'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_szr_version_last(server)

    def test_verify_script_execution_on_bootstrap(self, context: dict, cloud: Cloud, servers: dict,
                                                  event: str, script_name: str, user: str, exitcode: int,
                                                  output: str, stderr: bool):
        """Verify script execution on bootstrapping"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name=script_name,
                                             event=event,
                                             user=user,
                                             log_contains=output,
                                             std_err=stderr,
                                             exitcode=exitcode)

    @pytest.mark.chef
    @pytest.mark.run_only_if(family=['!windows'])
    def test_verify_chef_execution(self, cloud: Cloud, servers: dict):
        """Verify chef executed normally"""
        server = servers['M1']
        node = cloud.get_node(server)
        lib_server.assert_file_exist(node, file_path='/root/chef_solo_result')
        lib_server.assert_file_exist(node, file_path='/root/chef_hostup_result')
        lib_node.assert_process_has_options(cloud, server, process='memcached', options='-m 1024')
        # orchestration.assert_recipes_in_runlist(server, recipes=['memcached', 'revizorenv'])

    def test_execute_scripts(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                             script_name: str, synchronous: bool, is_local: bool, output: str, stderr: bool):
        """Verify script execution on running instance"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name=script_name,
                                  synchronous=synchronous, is_local=is_local)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name=script_name,
                                             log_contains=output,
                                             std_err=stderr,
                                             new_only=True)

    @pytest.mark.run_only_if(family=['!windows'])
    @pytest.mark.parametrize('user, exists',
                             [
                                 ('', True),
                                 ('root', True),
                                 ('revizor', True),
                                 ('unknown', False),
                                 # ('a' * 255, False), SCALRCORE-10468
                             ],
                             ids=[
                                 'empty',
                                 'root',
                                 'revizor',
                                 'unknown',
                                 # 'a * 255', SCALRCORE-10468
                             ])
    def test_execute_scripts_user(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                                  user, exists):
        """Check script execution as user"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='env', user=user)
        user = user if user else 'root'
        contains = ("USER=%s" if exists else "no such user: '%s'") % user
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='env',
                                             log_contains=contains,
                                             user=user,
                                             std_err=not exists,
                                             new_only=True)

    @pytest.mark.restart
    @pytest.mark.run_only_if(family=['windows'])
    def test_restart_scalarizr_script(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Restart scalarizr during script execution"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server,
                                  script_name='windows sleep 60',
                                  synchronous=True)
        windows.agent_restart(cloud, server)
        windows.assert_szr_terminated_in_log(cloud, server)
        lib_node.assert_service_work(cloud, server, 'scalarizr')
        windows.assert_errors_in_szr_logs(cloud, server)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='windows sleep 60',
                                             new_only=True)

    def test_bootstrap_with_fail_script(self, context: dict, cloud: Cloud, farm: Farm):
        """Bootstrapping with broken script"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_script'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.FAILED)
        assert server.is_init_failed, "Server %s failed not on Initializing" % server.id
        lookup_substrings = ['hostUp',
                             'Multiplatform_exit_1.ps1&quot; exited with code 1' if CONF.feature.dist.is_windows
                              else 'Multiplatform_exit_1&quot; exited with code 1']
        fail_message = server.get_failed_status_message()
        assert all(map(lambda x: x in fail_message, lookup_substrings)),\
            "Unexpected Failed status message: %s" % fail_message

    @pytest.mark.run_only_if(family=['windows'])
    def test_scripting_gv_length(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check agent sets long GV and script executes"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['long_variables'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lib_server.execute_script(context, farm, server, script_name='GV length')
        for i in range(6):
            lib_server.assert_last_script_result(context, cloud, server,
                                                 name='GV length',
                                                 log_contains='rev_long_var_%s 4095' % i)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='GV length',
                                             log_contains='rev_very_long_var 8192')
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='GV length',
                                             log_contains='rev_nonascii_var 7')
