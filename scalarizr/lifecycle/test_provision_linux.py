import time

import pytest
import logging

from uuid import uuid4

from revizor2.cloud import Cloud
from revizor2.api import Farm
from revizor2.consts import ServerStatus, Platform
from revizor2.conf import CONF

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, provision

LOG = logging.getLogger(__name__)


class TestChefProvisionLinux:
    """ Linux server provision with chef
    """

    order = ('test_bootstrapping_chef_role',
             'test_checking_config_changes',
             'test_checking_deletion_chef_fixtures',
             'test_chef_solo_bootstrapping',
             'test_chef_bootstrap_failure',
             'test_bootstrapping_from_chef_role',
             'test_chef_bootstrapping_via_cookbooks_with_hostname_configured'
             )

    @pytest.mark.boot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_bootstrapping_chef_role(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping chef role firstly"""
        lib_farm.add_role_to_farm(context, farm, role_options=['chef'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        node = cloud.get_node(server)
        chef_client_cfg = "/etc/chef/client.rb"
        lib_server.assert_scalarizr_log_errors(cloud, server)
        lifecycle.assert_szr_version_last(server)
        lib_node.assert_process_has_options(cloud, server, process='memcached', options='-m 1024')
        lib_node.assert_process_has_options(cloud, server, process='chef-client', options='--daemonize')
        provision.assert_node_exists_on_chef_server(server)
        provision.assert_chef_node_name_equal_hostname(cloud, server)
        provision.assert_chef_log_contains_text(server, "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK")
        provision.assert_param_exists_in_config(
            node,
            config_name=chef_client_cfg,
            param_name="verbose_logging",
            param_value="false")
        lib_server.assert_file_exist(node, f'/var/chef/lock')
        provision.assert_param_exists_in_config(
            node,
            config_name=chef_client_cfg,
            param_name="log_level",
            param_value=":fatal")
        provision.assert_chef_log_not_contains_level(server, ['INFO', 'DEBUG'])

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
    def test_checking_deletion_chef_fixtures(self, farm: Farm, servers: dict):
        """Verify Scalr delete chef-fixtures"""
        server = servers['M1']
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')
        provision.assert_node_exists_on_chef_server(server, exist=False)

    @pytest.mark.boot
    @pytest.mark.parametrize('role_options',
                             [
                                 'chef-solo-custom_url',
                                 'chef-solo-private',
                                 'chef-solo-public',
                                 'chef-solo-public-branch',
                             ])
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_chef_solo_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, role_options: str):
        """Bootstrapping role with chef-solo"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=[role_options])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        node = cloud.get_node(server)
        lib_server.assert_file_exist(node, f'/root/{role_options}')
        provision.assert_script_data_deleted(cloud, server)
        lib_server.assert_file_exist(node, f'/var/chef/lock')

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

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_bootstrapping_from_chef_role(self, context: dict, cloud: Cloud, farm: Farm):
        """Bootstrapping from chef role"""
        lib_farm.clear(farm)
        farm.terminate()
        lib_farm.add_role_to_farm(context, farm, role_options=['chef-role'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lib_server.assert_scalarizr_log_errors(cloud, server)
        lifecycle.assert_szr_version_last(server)
        provision.assert_node_exists_on_chef_server(server)
        provision.assert_chef_node_name_equal_hostname(cloud, server)
        provision.assert_chef_log_contains_text(server, "revizor_chef_variable=REVIZOR_CHEF_VARIABLE_VALUE_WORK")

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_chef_bootstrapping_via_cookbooks_with_hostname_configured(self, context: dict, cloud: Cloud, farm: Farm):
        """Chef bootstrapping with hostname configured via cookbooks"""
        hostname = f'hostname-LIX{uuid4().hex[16:24]}'
        lib_farm.clear(farm)
        farm.terminate()
        context['chef_hostname_for_cookbook'] = hostname
        lib_farm.add_role_to_farm(context, farm, role_options=['chef-hostname'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lib_server.assert_scalarizr_log_errors(cloud, server)
        server.reload()
        assert server.hostname == hostname, \
            f'Hostname on server "{server.hostname}" != chef hostname configured via the cookbook "{hostname}"'


class TestAnsibleTowerProvisionLinux:
    """ Linux server provision with Ansible Tower
    """

    order = (
             'test_bootstrapping_role_with_at',
             'test_launch_at_job',
             'test_verify_at_job_execution',
             'test_verify_node_deletion_from_at'
             )

    @pytest.fixture(scope="class", autouse=True)
    def setup_ansible_tower_configuration(self, context: dict):
        """Setup Ansible Tower bootstrap configurations"""
        at_group_type = 'regular'
        at_group_name = 'G1'
        at_credentials_name = f'linux-cred-{time.strftime("%a-%d-%b-%Y-%H:%M:%S:%MS")}'
        context['credentials_name'] = at_credentials_name
        at_template_name = 'Revizor_linux_Job_Template_with_Extra_Var'

        provision.set_at_server_id(context)
        provision.create_copy_at_inventory(context, 'Revizor_linux')
        provision.create_at_group(
            context,
            group_type=at_group_type,
            group_name=at_group_name)
        provision.assert_at_group_exists_in_inventory(context['at_group_id'])
        provision.create_at_credential(context, 'linux')
        provision.assert_credential_exists_on_at_server(
            credentials_name=at_credentials_name,
            key=context[f'at_cred_primary_key_{at_credentials_name}'])
        provision.set_at_job_template_id(context, at_template_name)
        if CONF.feature.dist.id in ['ubuntu-16-04', 'ubuntu-18-04']:
            at_python_path = 'at_python_path: 3'
        else:
            at_python_path = 'at_python_path: null'
        context['at_python_path'] = at_python_path

    @pytest.mark.boot
    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_bootstrapping_role_with_at(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping role with Ansible Tower"""
        lib_farm.add_role_to_farm(context, farm, role_options=['ansible-tower', 'ansible-orchestration'])
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lib_server.assert_scalarizr_log_errors(cloud, server)
        lifecycle.assert_szr_version_last(server)
        provision.assert_hostname_exists_on_at_server(server)
        provision.assert_at_user_on_server(cloud, server, 'scalr-ansible')

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_launch_at_job(self, context: dict, cloud: Cloud, servers: dict):
        """Launch Ansible Tower Job from AT server"""
        server = servers['M1']
        provision.launch_ansible_tower_job(context, 'Revizor_linux_Job_Template', job_result='successful')
        provision.assert_deployment_work(cloud, server, expected_output='dir1')

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_verify_at_job_execution(self, context: dict, cloud: Cloud, servers: dict, farm: Farm):
        """Verify AT job execution on event: HostUp, RebootComplete, ResumeComplete"""
        server = servers['M1']
        lib_server.assert_last_script_result(
            context, cloud, server,
            name='Revizor_linux_Job_Template_with_Extra_Var',
            event='HostUp',
            exitcode=0,
            log_contains='Extra_Var_HostUp')
        lib_server.execute_server_action(server, 'reboot')
        lib_server.assert_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        lib_server.assert_last_script_result(
            context, cloud, server,
            name='Revizor_linux_Job_Template_with_Extra_Var',
            event='RebootComplete',
            exitcode=0,
            log_contains='Extra_Var_RebootComplete')
        lib_server.execute_server_action(server, 'suspend')
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.SUSPENDED)
        lib_server.execute_server_action(server, 'resume')
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RESUMING)
        lib_server.wait_server_status(context, cloud, farm, server=server, status=ServerStatus.RUNNING)
        lib_server.assert_last_script_result(
            context, cloud, server,
            name='Revizor_linux_Job_Template_with_Extra_Var',
            event='ResumeComplete',
            exitcode=0,
            log_contains='Extra_Var_ResumeComplete')
        lib_server.assert_scalarizr_log_errors(cloud, server)

    @pytest.mark.run_only_if(
        platform=[Platform.EC2, Platform.GCE, Platform.VMWARE, Platform.OPENSTACK, Platform.RACKSPACENGUS])
    def test_verify_node_deletion_from_at(self, farm: Farm, servers: dict):
        """Verify Scalr delete node from AT server"""
        farm.terminate()
        lib_server.wait_servers_state(farm, 'terminated')
        server = servers['M1']
        provision.assert_hostname_exists_on_at_server(server, negation=True)

