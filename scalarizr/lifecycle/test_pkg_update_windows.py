import time

import pytest

from revizor2.api import Farm, Role
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform

from scalarizr.lib import role as lib_role
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import update, lifecycle


class TestPkgUpdateWindows:
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

    @pytest.fixture(autouse=True)
    def cleanup(self, farm: Farm):
        farm.terminate()
        lib_farm.clear(farm)

    @pytest.mark.parametrize('branch', ['stable', 'latest'])
    def test_update_from_branch_on_startup(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, branch: str):
        """Update scalarizr from release to branch on startup"""
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=Role.get(role['role']['id']))
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud, custom_branch=branch)
        time.sleep(120)
        lib_server.execute_server_action(server, 'reboot', hard=True)
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_node.reboot_scalarizr(cloud, server)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='update')

    @pytest.mark.parametrize('branch', ['stable'])
    def test_update_to_branch_from_ui(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, branch: str):
        """Update scalarizr from release to branch via UI"""
        farm.terminate()
        lib_farm.clear(farm)
        farm.launch()
        farm_role = lib_farm.add_role_to_farm(context, farm, role_options=['branch_{}'.format(branch)])
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.assert_szr_version_last(server, branch=branch)
        lib_role.change_branch_in_farm_role(farm_role, 'system')
        update.start_scalarizr_update_via_ui(server)
        update.wait_szrupd_status(server, 'completed')
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='HostUpdate', server=server)
        lifecycle.assert_szr_version_last(server, branch='system')
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_node.reboot_scalarizr(cloud, server)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_branch_to_stable_on_startup(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Update scalarizr from branch to stable on startup"""
        farm.terminate()
        lib_farm.clear(farm)
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        lib_farm.add_role_to_farm(context, farm, role=Role.get(role['role']['id']), role_options=['branch_stable'])
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud)
        time.sleep(120)
        lib_server.execute_server_action(server, 'reboot', hard=True)
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_node.reboot_scalarizr(cloud, server)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_stable_to_branch_on_startup_and_new_package(self, context: dict, cloud: Cloud, farm: Farm,
                                                                     servers: dict):
        """Update scalarizr from stable to branch on startup with new pkg"""
        farm.terminate()
        lib_farm.clear(farm)
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        farm_role = lib_farm.add_role_to_farm(context, farm, role=Role.get(role['role']['id']))
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud, custom_branch='stable')
        time.sleep(120)
        lib_server.execute_server_action(server, 'reboot', hard=True)
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        update.assert_scalarizr_version(server, cloud, szr_ver)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        lib_role.change_branch_in_farm_role(farm_role, context['branch_copy_name'])
        update.start_scalarizr_update_via_ui(server)
        update.wait_szrupd_status(server, 'in-progress')
        update.wait_szrupd_status(server, 'completed')
        lifecycle.assert_szr_version_last(server, branch=context['branch_copy_name'])
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_node.reboot_scalarizr(cloud, server)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='update')

    def test_update_from_branch_to_branch_on_startup_and_new_package(self, context: dict, cloud: Cloud, farm: Farm,
                                                                     servers: dict):
        """Update scalarizr from branch to branch on startup with new pkg"""
        farm.terminate()
        lib_farm.clear(farm)
        image = update.get_clean_image(cloud)
        role = lib_role.create_role(image)
        farm.launch()
        farm_role = lib_farm.add_role_to_farm(context, farm, role=Role.get(role['role']['id']))
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.PENDING)
        szr_ver = lib_node.install_scalarizr_to_server(server, cloud)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        lib_role.change_branch_in_farm_role(farm_role, context['branch_copy_name'])
        lib_server.execute_server_action(server, 'reboot', hard=True)
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING, server=server)
        lifecycle.assert_szr_version_last(server, branch=context['branch_copy_name'])
        update.assert_scalarizr_version(server, cloud, szr_ver)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        update.create_branch_copy(context, branch='system')
        update.waiting_new_package(context)
        lib_role.change_branch_in_farm_role(farm_role, context['branch_copy_name'])
        update.start_scalarizr_update_via_ui(server)
        update.wait_szrupd_status(server, 'in-progress')
        update.wait_szrupd_status(server, 'completed')
        lifecycle.assert_szr_version_last(server, branch=context['branch_copy_name'])
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_node.reboot_scalarizr(cloud, server)
        lib_server.execute_script(context, farm, server, script_name='Windows ping-pong. CMD', synchronous=True)
        lib_server.assert_last_script_result(context, cloud, server,
                                             name='Windows ping-pong. CMD',
                                             log_contains='pong',
                                             new_only=True)
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='debug')
        lib_server.assert_scalarizr_log_errors(cloud, server, log_type='update')
