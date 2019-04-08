import pytest

from revizor2.conf import CONF
from revizor2.api import Farm, Role, IMPL
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server

from .common import discovery, lifecycle


class TestDiscoveryManager:
    order = (
        'test_import_server',
        'test_deploy_agent'
    )

    @pytest.mark.run_only_if(platform=['ec2', 'gce'])
    def test_import_server(self, context: dict, cloud: Cloud, farm: Farm):
        """Import cloud server to Scalr"""
        farm.launch()
        node = discovery.run_server_in_cloud(cloud)
        location = CONF.feature.platform.location
        instance_id = node.id

        if CONF.feature.platform.is_gce:
            location = node.extra['zone'].name
            instance_id = node.name

        role_id = IMPL.discovery_manager.get_system_role_id(
            node.cloud._name,
            location,
            CONF.feature.dist.id
        )
        role = Role(id=role_id)
        farm_role_id = lib_farm.add_role_to_farm(context, farm, role=role).id
        IMPL.discovery_manager.import_server(node.cloud._name, farm_role_id, instance_id=instance_id)
        farm.roles.reload()
        assert farm.roles[0].role_id == str(role_id)
        assert len(farm.roles) == 1
        assert len(farm.roles[0].servers) == 1
        assert farm.roles[0].servers[0].cloud_server_id == instance_id
        lifecycle.validate_server_status(farm.roles[0].servers[0], ServerStatus.RUNNING)

    @pytest.mark.run_only_if(platform=['ec2', 'gce'])
    def test_deploy_agent(self, context: dict, cloud: Cloud, farm: Farm):
        """Deploy Agent to imported server"""
        server = farm.roles[0].servers[0]
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
        lib_node.deploy_agent(server, cloud)
        lib_node.handle_agent_status(server)
        lifecycle.validate_scalarizr_version(server, 'latest')
        lib_server.execute_state_action(server, 'reboot')
        lib_server.validate_server_message(cloud, farm, msgtype='in', msg='RebootFinish', server=server)
        lib_server.execute_script(context, farm, server, script_name='Linux ping-pong', synchronous=True)
        lib_server.validate_last_script_result(context, cloud, server,
                                               name='Linux ping-pong',
                                               log_contains='pong',
                                               new_only=True)
