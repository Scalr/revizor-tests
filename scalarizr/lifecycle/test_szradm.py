import json

import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle


class TestSzrAdm:
    """Test scalarizr admin check backward compatibility"""

    order = (
        'test_bootstrapping',
        'test_queryenv_latest_version',
        'test_queryenv_list_roles',
        'test_queryenv_farm_role_params',
        'test_queryenv_list_virtualhosts',
        'test_fire_event'
    )

    @pytest.mark.boot
    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstrapping"""
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_scalarizr_version(server)

    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_queryenv_latest_version(self, cloud: Cloud, servers: dict):
        """Verify szradm queryenv get-latest-version"""
        szradm_latest_version = "2015-04-10"
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        result = lifecycle.szradm_execute_command(
            command="szradm queryenv get-latest-version",
            cloud=cloud,
            server=server
        )
        assert result.get('version') == szradm_latest_version

    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_queryenv_list_roles(self, cloud: Cloud, farm: Farm, servers: dict):
        """Verify szradm queryenv list-roles"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        result = lifecycle.szradm_execute_command(
            command="szradm queryenv list-roles",
            cloud=cloud,
            server=server)
        assert farm.roles[0].name == result['roles'][0]['name']

    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_queryenv_farm_role_params(self, farm: Farm, cloud: Cloud, servers: dict):
        """Verify szradm queryenv list-roles farm-role-id=farm_role_id"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        result = lifecycle.szradm_execute_command(
            command=f"szradm queryenv list-roles farm-role-id={farm.roles[0].id}",
            cloud=cloud,
            server=server)
        assert farm.roles[0].name == result['roles'][0]['name']

    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_queryenv_list_virtualhosts(self, cloud: Cloud, servers: dict):
        """Verify szradm queryenv list-virtualhosts"""
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        result = lifecycle.szradm_execute_command(
            command="szradm queryenv list-virtualhosts",
            cloud=cloud,
            server=server
        )
        assert not result['vhosts']

    @pytest.mark.run_only_if(platform=['ec2', 'vmware', 'gce', 'cloudstack', 'rackspaceng', 'openstack', 'azure'])
    def test_fire_event(self, farm: Farm, cloud: Cloud, servers: dict):
        """Verify szradm --fire-event event one=1 two=2 three=3"""
        server = servers['M1']
        message_name = "FireEvent"
        event_params = dict(
            one='one',
            two='two',
            three='three'
        )
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lifecycle.szradm_execute_command(
            command="szradm --fire-event event one={one} two={two} three={three}".format(**event_params),
            cloud=cloud,
            server=server,
            format_output=False
        )
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg=message_name, server=server)
        server_messages = list(filter(lambda m: m.name == message_name, server.messages))
        result = json.loads(lifecycle.szradm_execute_command(
            command=f"szradm md {server_messages[0].id} --json",
            cloud=cloud,
            server=server,
            format_output=False
        ))
        assert result['body']['params'] == event_params
