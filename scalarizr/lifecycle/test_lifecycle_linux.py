from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from .steps import lifecycle_steps, szradm_steps


class TestLifecycleLinux:
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm):
        lib_farm.add_role_to_farm(context, farm, role_options=['storages', 'noiptables'])
        farm.launch()
        server = lib_server.wait_status(context, cloud, farm, status=ServerStatus.RUNNING)
        context['server'] = server
        lifecycle_steps.validate_instance_vcpus_info(server)
        lib_server.assert_scalarizr_version(server)
        lib_server.verify_hostname_is_valid(server)
        lib_server.verify_ports_in_iptables(cloud, server, [8008, 8010, 8012, 8013, 8014], invert=True)
        lifecycle_steps.assert_server_message_count(context=context, server=server, msg='BlockDeviceMounted')

    def test_szradm_listroles(self, context: dict, cloud: Cloud):
        server = context['server']
        result = szradm_steps.run_command(cloud, server, 'szradm -q list-roles')
        assert result['response']['roles']['role']['hosts']['host']['external-ip'] == server.public_ip, \
            f'Not see server public ip in szradm response: {result}'
        result = szradm_steps.run_command(cloud, server, 'szradm --queryenv get-latest-version')
        value, count = szradm_steps.get_key(result, 'version')
        assert count == 1, f'The key "version" does not exists or number of entries do not match on {server.id}'
        result = szradm_steps.run_command(cloud, server, 'szradm list-messages')
        assert 'HostUp' in result['name'], \
            f'Value "HostUp" does not exist in column "name", all values: {result["name"]}'
