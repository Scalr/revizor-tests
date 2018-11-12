import json
import logging
import time

from revizor2 import CONF
from revizor2.api import Server
from revizor2.cloud import Cloud
from revizor2.consts import Dist
from revizor2.helpers.parsers import get_repo_url, parser_for_os_family
from scalarizr.lib.util.szradm_resultsparser import SzrAdmResultsParser

LOG = logging.getLogger(__name__)


def get_last_version(dist: str, branch: str) -> str:
    if '.' in branch and branch.replace('.', '').isdigit():
        last_version = branch
    else:
        # Get custom repo url
        os_family = Dist(dist).family
        index_url = get_repo_url(os_family, branch)
        LOG.debug(f'Check package from index_url: {index_url}')
        repo_data = parser_for_os_family(dist)(index_url=index_url)
        if os_family == 'coreos':
            versions = repo_data
        else:
            versions = [package['version'] for package in repo_data if package['name'] == 'scalarizr']
        versions.sort(reverse=True)
        last_version = versions[0].strip()
        if last_version.endswith('-1'):
            last_version = last_version[:-2]
    return last_version


def get_installed_version(server: Server) -> str:
    """Get installed scalarizr version"""
    for _ in range(10):
        try:
            update_status = server.upd_api.status(cached=False)
            break
        except Exception:
            time.sleep(3)
    else:
        raise AssertionError('Can\'t get access to update client 5 times (15 seconds)')
    if not update_status['state'] == 'noop' and update_status['prev_state'] == 'completed':
        assert update_status['state'] == 'completed', \
            f'Update client not in normal state. ' \
            f'State = "{update_status["state"]}", ' \
            f'Previous state = "{update_status["prev_state"]}"'
    installed_version = update_status['installed'].strip()
    if installed_version.endswith('-1'):
        installed_version = installed_version[:-2]
    return installed_version


def run_szradm_command(cloud: Cloud, server: Server, command: str) -> dict:
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        LOG.info(f'Execute a command: {command} on a remote host: {server.id}')
        if command == 'szradm q list-farm-role-params':
            farm_role_id = json.loads(conn.run('szradm q list-roles --format=json').std_out)['roles'][0]['id']
            command = f'szradm q list-farm-role-params farm-role-id={farm_role_id}'
        if CONF.feature.dist.id == 'coreos':
            command = 'PATH=$PATH:/opt/bin; ' + command
        out = conn.run(command)
        if out.status_code:
            raise AssertionError(f"Command: {command} was not executed properly. An error has occurred:\n{out.std_err}")
        LOG.debug(f'Parsing a command result: {out.std_out}')
        result = SzrAdmResultsParser.parser(out.std_out)
        LOG.debug(f'Command result was successfully parsed on a remote host:{server.id}\n{result}')
    return result
