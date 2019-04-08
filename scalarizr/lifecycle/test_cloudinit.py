import pytest

from revizor2.conf import CONF
from revizor2.api import Farm, Role, IMPL
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server

from .common import discovery, lifecycle


class TestCloudinit:
    order = (
        'test_start_cloudinit_server',
        'test_rebundle_cloudinit_server'
    )

    def test_start_cloudinit_server(self, context: dict, cloud: Cloud, farm: Farm):
        node = discovery.run_server_in_cloud(cloud)

    def test_rebundle_cloudinit_server(self, context: dict, cloud: Cloud, farm: Farm):
        pass
