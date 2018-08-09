import logging

from revizor2.api import Server
from revizor2.cloud import Cloud
import scalarizr.lib.agent as lib_agent
from scalarizr.lib.util.szradm_resultsparser import SzrAdmResultsParser

LOG = logging.getLogger(__name__)


def get_key(szradm_response: dict, pattern: str) -> tuple:
    key_value = list(SzrAdmResultsParser.get_values_by_key(szradm_response, pattern))
    key_count = len(key_value[0] if isinstance(key_value[0], list) else key_value)
    return key_value, key_count


def validate_external_ip(cloud: Cloud, server: Server):
    result = lib_agent.run_szradm_command(cloud, server, command='szradm -q list-roles')
    assert result['response']['roles']['role']['hosts']['host']['external-ip'] == server.public_ip, \
        f'Not see server public ip in szradm response: {result}'


def validate_key_records(cloud: Cloud, server: Server, command: str, key: str, count: int = None, record: str = None):
    result = lib_agent.run_szradm_command(cloud, server, command)
    if count is not None:
        _, actual_count = get_key(result, key)
        assert actual_count == count, \
            f'The key "{key}" does not exist or number of entries does not match on {server.id}. ' \
            f'Actual: {actual_count}, expected: {count}'
    if record is not None:
        assert record in result[key], \
            f'Value "{record}" does not exist in column "{key}". All values: {result[key]}'
