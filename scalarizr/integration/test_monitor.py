import pytest

from revizor2.conf import CONF
from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform

from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server

from .common.monitor import assert_push_stats_in_influx, assert_stats_received


#TODO: SCALRCORE-12264
class TestMonitor:
    order = (
        'test_push_statistics'
    )

    @pytest.mark.run_only_if(platform=[Platform.GCE])
    def test_push_statistics(self, farm: Farm, context: dict, cloud: Cloud, servers: dict, testenv):
        """Verify push statistics work in scalarizr master"""
        roles = {}
        CONF.feature.platform = Platform('gce')
        CONF.feature.branch = 'master'
        for dist in ('ubuntu1604', 'centos7', 'win2012'):
            roles[dist] = lib_farm.add_role_to_farm(context, farm, dist=dist)
        farm.launch()
        for index, role in enumerate(roles.values()):
            servers[f'A{index}'] = lib_server.wait_server_status(context, cloud, farm, role=role, status=ServerStatus.RUNNING)
        for server in servers.values():
            lib_server.assert_scalarizr_log_errors(cloud, server)
        assert_stats_received(servers, testenv, 'Pushing')
        assert_push_stats_in_influx(testenv, servers)


