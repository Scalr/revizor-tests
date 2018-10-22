import logging
import time

import requests

import scalarizr.lib.server as lib_server
from revizor2 import CONF
from revizor2.api import Cloud, Server
from revizor2.helpers.parsers import get_repo_url, parser_for_os_family
from revizor2.utils import wait_until

LOG = logging.getLogger(__name__)


def reboot_scalarizr(cloud: Cloud, server: Server):
    if CONF.feature.dist.is_systemd:
        cmd = "systemctl restart scalarizr"
    else:
        cmd = "/etc/init.d/scalarizr restart"
    node = cloud.get_node(server)
    node.run(cmd)
    LOG.info('Scalarizr restart complete')
    time.sleep(15)


def validate_scalarizr_log_contains(cloud: Cloud, server: Server, message: str):
    node = cloud.get_node(server)
    LOG.info('Check scalarizr log')
    wait_until(lib_server.check_text_in_scalarizr_log, timeout=300, args=(node, message),
               error_text='Not see %s in debug log' % message)


def execute_command(cloud: Cloud, server: Server, command: str):
    if (command.startswith('scalarizr') or command.startswith('szradm')) and CONF.feature.dist.id == 'coreos':
        command = '/opt/bin/' + command
    node = cloud.get_node(server)
    LOG.info('Execute command on server: %s' % command)
    node.run(command)


def get_scalaraizr_latest_version(branch: str) -> str:
    os_family = CONF.feature.dist.family
    index_url = get_repo_url(os_family, branch)
    LOG.debug('Check package from index_url: %s' % index_url)
    repo_data = parser_for_os_family(CONF.feature.dist.mask)(index_url=index_url)
    versions = [package['version'] for package in repo_data if
                package['name'] == 'scalarizr'] if os_family != 'coreos' else repo_data
    versions.sort(reverse=True)
    return versions[0]


def validate_scalarizr_version(server: Server, branch: str = None):
    """
    Argument branch can be system or role.
    System branch - CONF.feature.branch
    Role branch - CONF.feature.to_branch
    """
    if branch == 'system' or not branch:
        branch = CONF.feature.branch
    elif branch == 'role':
        branch = CONF.feature.to_branch
    if '.' in branch and branch.replace('.', '').isdigit():
        last_version = branch
    else:
        # Get custom repo url
        last_version = get_scalaraizr_latest_version(branch)
        if last_version.strip().endswith('-1'):
            last_version = last_version.strip()[:-2]
    LOG.debug('Last scalarizr version %s for branch %s' % (last_version, branch))
    # Get installed scalarizr version
    for _ in range(10):
        try:
            update_status = server.upd_api.status(cached=False)
            installed_version = update_status['installed']
            if installed_version.strip().endswith('-1'):
                installed_version = installed_version.strip()[:-2]
            break
        except requests.exceptions.HTTPError:
            time.sleep(3)
    else:
        raise AssertionError('Can\'t get access to update client 5 times (15 seconds)')
    LOG.debug('Last scalarizr version from update client status: %s' % update_status['installed'])
    if not update_status['state'] == 'noop' and update_status['prev_state'] == 'completed':
        assert update_status['state'] == 'completed', \
            'Update client not in normal state. Status = "%s", Previous state = "%s"' % \
            (update_status['state'], update_status['prev_state'])
    assert last_version == installed_version, \
        'Server not has last build of scalarizr package, installed: %s last_version: %s' % \
        (installed_version, last_version)
