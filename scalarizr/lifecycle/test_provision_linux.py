import json
import pytest
import logging

from revizor2.cloud import Cloud
from revizor2.api import Farm
from revizor2.consts import ServerStatus, Platform

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, provision

LOG = logging.getLogger(__name__)


class TestProvisionLinux:
    """ Linux server provision with chef and ansible tower
    """

    order = ('test_bootstrapping_chef_role',
             'test_checking_config_changes',
             'test_checking_deletion_chef_fixtures',
             'test_chef_solo_bootstrapping',
             'test_chef_bootstrap_failure'
             )

    @pytest.mark.boot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_bootstrapping_chef_role(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping chef role firstly"""
        lib_farm.add_role_to_farm(context, farm, role_options=['chef'])
        farm.launch()
        #server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        #servers['M1'] = server
        #lib_server.assert_scalarizr_log_errors(cloud, server)
        #lifecycle.assert_szr_version_last(server)
        #lib_node.assert_process_has_options(cloud, server, process='memcached', options='-m 1024')
        #lib_node.assert_process_has_options(cloud, server, process='chef-client', options='--daemonize')
        #provision.assert_node_exists_on_chef_server(server)
        #provision.assert_chef_node_name_equal_hostname(cloud, server)
        #provision.assert_chef_log_contains_text(server, "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK")

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_checking_config_changes(self, cloud: Cloud, servers: dict):
        """Checking config changes: INTERVAL"""
        server = servers['M1']
        node = cloud.get_node(server)
        interval = 15
        provision.change_chef_client_interval_value(node, interval)
        provision.assert_chef_client_interval_value(node, interval)
        provision.assert_chef_runs_time(node, interval)

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_checking_deletion_chef_fixtures(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Verify Scalr delete chef-fixtures"""
        server = servers['M1']
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')
        provision.assert_node_exists_on_chef_server(server, exist=False)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lib_node.assert_process_has_options(cloud, server, process='memcached', options='-m 1024')
        lib_node.assert_process_has_options(cloud, server, process='chef-client', options='--daemonize')
        provision.assert_chef_node_name_equal_hostname(cloud, server)

    #@pytest.mark.boot
    @pytest.mark.parametrize('role_options', ['chef-solo-private', 'chef-solo-public', 'chef-solo-public-branch'])
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_chef_solo_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, role_options: str):
        """Bootstrapping role with chef-solo"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=[role_options])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        node = cloud.get_node(server)
        lib_server.assert_file_exist(node, f'/root/{role_options}')
        provision.assert_script_data_deleted(cloud, server)

    @pytest.mark.boot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_chef_bootstrap_failure(self, context: dict, cloud: Cloud, farm: Farm):
        """Chef bootstrap failure"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['chef-fail'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.FAILED)
        lib_server.validate_failed_status_message(server, "beforeHostUp", "/usr/bin/chef-client exited with code 1")
        provision.assert_chef_log_contains_text(server, "ERROR: undefined method `fatal!'")
        provision.assert_chef_bootstrap_failed(cloud, server)








