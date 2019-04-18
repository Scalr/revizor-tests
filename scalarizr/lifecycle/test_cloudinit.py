import pytest

from revizor2.api import Farm, Role
from revizor2.cloud import Cloud, Platform
from revizor2.consts import ServerStatus

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lib import role as lib_role
from scalarizr.lifecycle.common import rebundle

from .common import discovery, lifecycle, cloudinit


class TestCloudinit:
    order = (
        'test_start_cloudinit_server',
        'test_rebundle_cloudinit_server'
    )

    @pytest.mark.run_only_if(platform=[Platform.EC2])
    def test_start_cloudinit_server(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Check cloudinit server started"""
        node = discovery.run_server_in_cloud(cloud)
        cloudinit.assert_cloudinit_installed(node)
        image = lib_node.create_image_from_node(node, cloud)
        role = lib_role.create_role(image, non_scalarized=True, has_cloudinit=True)
        lib_farm.add_role_to_farm(context, farm, role=Role.get(role['role']['id']))
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.assert_vcpu_count(server)
        lifecycle.assert_szr_version_last(server)

    @pytest.mark.run_only_if(platform=[Platform.EC2])
    def test_rebundle_cloudinit_server(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Verify cloudinit server rebundling work"""
        bundle_id = rebundle.start_server_rebundle(servers['M1'])
        rebundle.assert_bundle_task_created(servers['M1'], bundle_id)
        role_id = rebundle.wait_bundle_complete(servers['M1'], bundle_id)
        farm.clear_roles()
        lib_farm.add_role_to_farm(context, farm, role=Role.get(role_id))
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        lifecycle.assert_szr_version_last(server)
        lib_server.assert_scalarizr_log_errors(cloud, server)
