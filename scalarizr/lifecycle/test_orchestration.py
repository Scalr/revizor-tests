import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, orchestration


class TestOrchestration:
    """
    Linux orchestration feature test
    """

    order = ('test_bootstrapping',
             'test_verify_script_execution_on_bootstrap',
             'test_verify_chef_execution',
             'test_execute_scripts_on_linux',
             'test_execute_scripts_user',
             'test_bootstrap_with_fail_script')

    @pytest.mark.boot
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['orchestration', 'chef'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_scalarizr_version(server)

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
    def test_verify_script_execution_on_bootstrap(self, context: dict, cloud: Cloud, servers: dict,
                                                  event: str, script_name: str, user: str, exitcode: int,
                                                  stdout: str, stderr: str):
        """Verify script execution on bootstrapping"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               event=event,
                                               user=user,
                                               log_contains=stdout,
                                               std_err=stderr,
                                               exitcode=exitcode)

    @pytest.mark.chef
    def test_verify_chef_execution(self, cloud: Cloud, servers: dict):
        """Verify chef executed normally"""
        server = servers['M1']
        lib_server.validate_file_exists(cloud, server, file_path='/root/chef_solo_result')
        lib_server.validate_file_exists(cloud, server, file_path='/root/chef_hostup_result')
        lib_node.validate_process_options(cloud, server, process='memcached', options='-m 1024')
        orchestration.verify_recipes_in_runlist(server, recipes=['memcached', 'revizorenv'])

    @pytest.mark.parametrize("script_name, synchronous, is_local, output",
                             [
                                 ("Linux ping-pong", False, False, "pong"),
                                 ("Linux ping-pong", True, False, "pong"),
                                 ("/home/revizor/local_script.sh", True, True,
                                  "Local script work!; USER=root; HOME=/root"),
                                 ("/home/revizor/local_script.sh", False, True,
                                  "Local script work!; USER=root; HOME=/root"),
                                 ("https://gist.githubusercontent.com/Theramas/5b2a9788df316606f72883ab1c3770cc/raw"
                                  "/3ae1a3f311d8e43053fbd841e8d0f17daf1d5d66/multiplatform", False, True,
                                  "Multiplatform script successfully executed"),
                                 ("Cross-platform script", False, False, "Multiplatform script successfully executed")
                             ],
                             ids=[
                                 "Ping-pong async",
                                 "Ping-pong sync",
                                 "Local sync",
                                 "Local async",
                                 "Multiplatform",
                                 "Cross-platform"
                             ])
    def test_execute_scripts_on_linux(self, context: dict, cloud: Cloud, farm: Farm, servers: dict,
                                      script_name: str, synchronous: bool, is_local: str, output: str):
        """Scripts executing on linux"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_server.execute_script(context, farm, server, script_name=script_name,
                                  synchronous=synchronous, is_local=is_local)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name=script_name,
                                               log_contains=output,
                                               std_err=False,
                                               new_only=True)

    @pytest.mark.parametrize('user, exists',
                             [
                                 ('', True),
                                 ('root', True),
                                 ('revizor', True),
                                 ('unknown', False),
                                 ('a' * 255, False),
                             ],
                             ids=[
                                 'empty',
                                 'root',
                                 'revizor',
                                 'unknown',
                                 'a * 255',
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

    def test_bootstrap_with_fail_script(self, context: dict, cloud: Cloud, farm: Farm):
        """Bootstrapping with broken script"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['failed_script'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.FAILED)
        assert server.is_init_failed, "Server %s failed not on Initializing" % server.id
        assert 'BeforeHostUp' and 'Multiplatform_exit_1&quot; exited with code 1' in server.get_failed_status_message(),\
            "Unexpected Failed status message: %s" % server.get_failed_status_message()
