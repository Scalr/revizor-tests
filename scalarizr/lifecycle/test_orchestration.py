import pytest

from revizor2.api import Farm, CONF
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, orchestration, windows
from scalarizr.lib.common import run_only_if


class TestOrchestration:
    """
    Linux orchestration feature test
    """

    order = ('test_bootstrapping',
             'test_verify_linux_script_execution_on_bootstrap',
             'test_verify_windows_script_execution_on_bootstrap',
             'test_verify_chef_execution',
             'test_execute_scripts_on_linux',
             'test_execute_scripts_on_windows',
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
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_scalarizr_version(server)

    @run_only_if(dist=['!windows-2008', '!windows-2012', '!windows-2016'])
    @pytest.mark.parametrize("event, script_name, user, exitcode, stdout, stderr",
                             [
                                 ("HostInit", "Revizor orchestration init", "root", 0, "", ""),
                                 ("HostInit", "/tmp/script.sh", "root", 1, "", ""),
                                 ("HostInit", "https://gist.githubusercontent.com", "root", 0,
                                  "Script runned from URL", ""),
                                 ("BeforeHostUp", "Linux ping-pong", "root", 0, "pong", ""),
                                 ("BeforeHostUp", "chef", "root", 0, '"HOME"=>"/root";"USER"=>"root"', ""),
                                 ("HostUp", "Linux ping-pong", "revizor2", 1, "", "STDERR: no such user: 'revizor2'"),
                                 ("HostUp", "/home/revizor/local_script.sh", "revizor", 0,
                                  "Local script work! User: revizor; USER=revizor; HOME=/home/revizor", ""),
                                 ("HostUp", "Linux ping-pong", "revizor", 0, "pong", ""),
                                 ("HostUp", "chef", "root", 0, "", ""),
                                 ("HostUp", "/bin/uname", "root", 0, "Linux", ""),
                                 ("HostUp", "https://gist.githubusercontent.com", "root", 0,
                                  "Multiplatform script successfully executed", ""),
                                 ("HostUp", "Sleep 10", "root", 130, "printing dot each second; .....", "")
                             ],
                             ids=[
                                 "HostInit Revizor orchestration init",
                                 "HostInit /tmp/script.sh",
                                 "HostInit script from url",
                                 "BeforeHostUp Ping-pong",
                                 "BeforeHostUp chef",
                                 "HostUp ping-pong with unexisting user",
                                 "HostUp local",
                                 "HostUp ping-pong",
                                 "HostUp chef",
                                 "HostUp /bin/uname",
                                 "HostUp multiplatform",
                                 "HostUp Sleep 10"
                             ])
    def test_verify_linux_script_execution_on_bootstrap(self, context: dict, cloud: Cloud, servers: dict,
                                                        event: str, script_name: str, user: str, exitcode: int,
                                                        stdout: str, stderr: str):
        """Verify script execution on bootstrapping for Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               event=event,
                                               user=user,
                                               log_contains=stdout,
                                               std_err=stderr,
                                               exitcode=exitcode)

    @run_only_if(dist=['windows-2008', 'windows-2012', 'windows-2016'])
    @pytest.mark.parametrize("event, script_name, exitcode, stdout",
                             [
                                 ("HostInit", "Windows_ping_pong_CMD", 0, "pong"),
                                 ("HostUp", "Windows_ping_pong_CMD", 0, "pong"),
                             ],
                             ids=[
                                 "HostInit Windows ping-pong",
                                 "HostUp Windows ping-pong"
                             ])
    def test_verify_windows_script_execution_on_bootstrap(self, context: dict, cloud: Cloud, servers: dict,
                                                          event: str, script_name: str, exitcode: int, stdout: str):
        """Verify script execution on bootstrapping for Windows"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               event=event,
                                               log_contains=stdout,
                                               exitcode=exitcode)

    @run_only_if(dist=['!windows-2008', '!windows-2012', '!windows-2016'])
    @pytest.mark.chef
    def test_verify_chef_execution(self, cloud: Cloud, servers: dict):
        """Verify chef executed normally"""
        server = servers['M1']
        lib_server.validate_file_exists(cloud, server, file_path='/root/chef_solo_result')
        lib_server.validate_file_exists(cloud, server, file_path='/root/chef_hostup_result')
        lib_node.validate_process_options(cloud, server, process='memcached', options='-m 1024')
        orchestration.verify_recipes_in_runlist(server, recipes=['memcached', 'revizorenv'])

    @run_only_if(dist=['!windows-2008', '!windows-2012', '!windows-2016'])
    @pytest.mark.parametrize("script_name, synchronous, is_local, output, std_err",
                             [
                                 ("Linux ping-pong", False, False, "pong", False),
                                 ("Linux ping-pong", True, False, "pong", False),
                                 ("/home/revizor/local_script.sh", True, True, "Local script work!; USER=root; HOME=/root", False),
                                 ("/home/revizor/local_script.sh", False, True, "Local script work!; USER=root; HOME=/root", False),
                                 ("https://gist.githubusercontent.com/Theramas/5b2a9788df316606f72883ab1c3770cc/raw"
                                  "/3ae1a3f311d8e43053fbd841e8d0f17daf1d5d66/multiplatform", False, True,
                                  "Multiplatform script successfully executed", False),
                                 ("Cross-platform script", False, False, "Multiplatform script successfully executed", False),
                                 ("Non ascii script", True, False, "Non_ascii_script", False),
                                 ("Non ascii script wrong interpreter", True, False, "Interpreter not found '/no/Ã§Ã£o'", True),
                                 ("non-ascii-output", True, False, "Ã¼", False),
                                 ("Verify hidden variable", True, False, "REVIZOR_HIDDEN_VARIABLE", False)
                             ],
                             ids=[
                                 "Ping-pong async",
                                 "Ping-pong sync",
                                 "Local sync",
                                 "Local async",
                                 "Multiplatform",
                                 "Cross-platform",
                                 "Non ascii script",
                                 "Non ascii script wrong interpreter",
                                 "Non ascii output",
                                 "Verify hidden variable"
                             ])
    def test_execute_scripts_on_linux(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                                      script_name: str, synchronous: bool, is_local: str, output: str, std_err: bool):
        """Scripts executing on Linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name=script_name,
                                  synchronous=synchronous, is_local=is_local)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               log_contains=output,
                                               std_err=std_err,
                                               new_only=True)

    @run_only_if(dist=['windows-2008', 'windows-2012', 'windows-2016'])
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    @pytest.mark.parametrize('script_name, synchronous, is_local, stdout, stderr',
                             [
                                 ('Windows ping-pong. CMD', True, False, 'pong', None),
                                 ('Windows ping-pong. CMD', False, False, 'pong', None),
                                 ('Windows ping-pong. PS', True, False, 'pong', None),
                                 ('Windows ping-pong. PS', False, False, 'pong', None),
                                 ('Cross-platform script', False, False, 'Multiplatform script successfully executed', None),
                                 ('https://gist.githubusercontent.com/gigimon/d233b77be7c04480c01a/raw'
                                  '/cd05c859209e1ff23961a371e0e2298ab3fb0257/gistfile1.txt', False, True, 'Script runned from URL', None),
                                 ('https://gist.githubusercontent.com/Theramas/48753f91f4af72be12c03c0485b27f7d/raw'
                                  '/97caf55e74c8db6c5bf96b6a29e48c043ac873ed/test', False, True, 'Multiplatform script successfully executed', None),
                                 ('Non ascii script wrong interpreter', False, False, None,
                                  "The only supported interpreters on Windows in first shebang are "
                                  "('powershell', 'cmd', 'cscript')"),
                                 ('Exit 1 with stdout message', False, False, 'Message in stdout section', None),
                                 ('Create local script', False, False, 'Directory: C:\; local_script.ps1', None),
                                 ('Non ascii script corect execution', False, False, 'abcdefg     HIJKLMNOP     qrs     TUVWXyz', None),
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
    def test_execute_scripts_on_windows(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                                        script_name: str, synchronous: bool, is_local: bool, stdout: str, stderr: str):
        """Scripts executing on Windows"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name=script_name,
                                  synchronous=synchronous, is_local=is_local)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               log_contains=stderr if stderr else stdout,
                                               std_err=bool(stderr),
                                               new_only=True)

    @run_only_if(dist=['!windows-2008', '!windows-2012', '!windows-2016'])
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
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name='env', user=user)
        user = user if user else 'root'
        contains = ("USER=%s" if exists else "no such user: '%s'") % user
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='env',
                                               log_contains=contains,
                                               user=user,
                                               std_err=not exists,
                                               new_only=True)

    @run_only_if(dist=['windows-2008', 'windows-2012', 'windows-2016'])
    @pytest.mark.restart
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

    def test_bootstrap_with_fail_script(self, context: dict, cloud: Cloud, farm: Farm):
        """Bootstrapping with broken script"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_script'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.FAILED)
        assert server.is_init_failed, "Server %s failed not on Initializing" % server.id
        lookup_substrings = ['BeforeHostUp',
                             'Multiplatform_exit_1.ps1&quot; exited with code 1' if CONF.feature.dist.is_windows
                              else 'Multiplatform_exit_1&quot; exited with code 1']
        fail_message = server.get_failed_status_message()
        assert all(map(lambda x: x in fail_message, lookup_substrings)),\
            "Unexpected Failed status message: %s" % fail_message

    @run_only_if(dist=['windows-2008', 'windows-2012', 'windows-2016'])
    @pytest.mark.platform('ec2', 'gce', 'openstack', 'azure')
    def test_scripting_gv_length(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check agent sets long GV and script executes"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['long_variables'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lib_server.execute_script(context, farm, server, script_name='GV length')
        for i in range(6):
            lib_server.validate_last_script_result(context, cloud, server,
                                                   name='GV length',
                                                   log_contains='rev_long_var_%s 4095' % i)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='GV length',
                                               log_contains='rev_very_long_var 8192')
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='GV length',
                                               log_contains='rev_nonascii_var 7')
