from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import lifecycle, szradm


class TestLifecycleLinux:
    """Linux server lifecycle"""
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstraping"""
        lib_farm.add_role_to_farm(context, farm, role_options=['storages', 'noiptables'])
        farm.launch()
        lib_server.wait_status(context, cloud, farm, status=ServerStatus.PENDING)
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        lifecycle.validate_vcpus_info(server)
        lifecycle.validate_scalarizr_version(server)
        lifecycle.validate_hostname(server)
        lifecycle.validate_iptables_ports(cloud, server, [8008, 8010, 8012, 8013, 8014], invert=True)
        lifecycle.validate_server_message_count(context, server, 'BlockDeviceMounted')

    def test_szradm_listroles(self, cloud: Cloud, servers: dict):
        """Verify szradm list-roles"""
        server = servers['M1']
        szradm.validate_external_ip(cloud, server)
        szradm.validate_key_records(cloud, server,
                                    command='szradm --queryenv get-latest-version',
                                    key='version',
                                    count=1)
        szradm.validate_key_records(cloud, server,
                                    command='szradm list-messages',
                                    key='name',
                                    record='HostUp')

    def test_attached_storages(self, servers: dict):
#         Given I have running server M1
        server = servers['M1']
        lifecycle.validate_server_status(server, ServerStatus.RUNNING)
#         Then I save volumes configuration in 'HostUp' message in M1

#         And disk types in role are valid
#         And directory '/media/diskmount' exist in M1
#         And directory '/media/raidmount' exist in M1
#         And directory '/media/partition' exist in M1
#         And I create 100 files in '/media/diskmount' in M1
#         And I create 100 files in '/media/raidmount' in M1