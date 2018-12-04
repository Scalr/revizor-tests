import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform

from scalarizr.lib import role as lib_role
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import update, lifecycle


class TestPkgUpdateLinux:
    """
    Package update test from stable/latest to branch
    """
    order = (
        'test_update_from_branch_on_startup',
        'test_update_to_branch_from_ui',
        'test_update_from_branch_to_stable_on_startup',
        'test_update_from_stable_to_branch_on_startup_and_new_package',
        'test_update_from_branch_to_branch_on_startup_and_new_package'
    )

    @pytest.mark.parametrize('branch', ['stable', 'latest'])
    def test_update_from_branch_on_startup(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, branch: str):
        """Update scalarizr from release to branch on startup"""
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=role)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud, custom_branch=branch)
        lib_server.execute_state_action(server, 'reboot', hard=True)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='update')

    @pytest.mark.parametrize('branch', ['stable', 'latest'])
    def test_update_to_branch_from_ui(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, branch: str):
        """Update scalarizr from release to branch via UI"""
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role_options=['branch_{}'.format(branch)])
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.validate_scalarizr_version(server, branch=branch)
        lib_role.change_branch_in_role_for_system('system')
        update.updating_scalarizr_by_scalr_ui(server)
        update.wait_updating_finish(server, 'completed')
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg='HostUpdate', server=server)
        lifecycle.validate_scalarizr_version(server, branch='system')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_branch_to_stable_on_startup(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Update scalarizr from branch to stable on startup"""
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=role, role_options=['branch_stable'])
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud)
        lib_server.execute_state_action(server, 'reboot', hard=True)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_stable_to_branch_on_startup_and_new_package(self, context: dict, cloud: Cloud, farm: Farm,
                                                                     servers: dict):
        """Update scalarizr from stable to branch on startup with new pkg"""
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=role)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud, custom_branch='stable')
        lib_server.execute_state_action(server, 'reboot', hard=True)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        lib_role.change_branch_in_role_for_system(context['branch_copy_name'])
        update.updating_scalarizr_by_scalr_ui(server)
        update.wait_updating_finish(server, 'completed')
        lifecycle.validate_scalarizr_version(server, branch='system')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_branch_to_branch_on_startup_and_new_package(self, context: dict, cloud: Cloud, farm: Farm,
                                                                     servers: dict):
        """Update scalarizr from branch to branch on startup with new pkg"""
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=role)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        lib_role.change_branch_in_role_for_system(context['branch_copy_name'])
        lib_server.execute_state_action(server, 'reboot', hard=True)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        lifecycle.validate_scalarizr_version(server, branch='system')
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        update.updating_scalarizr_by_scalr_ui(server)
        update.wait_updating_finish(server, 'completed')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.execute_state_action(server, 'reboot')
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.check_scalarizr_log_errors(cloud, server, log_type='update')
