import logging
from typing import List

from revizor2 import CONF
from revizor2.api import Server
import scalarizr.lib.agent as lib_agent
import scalarizr.lib.server as lib_server
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus

LOG = logging.getLogger(__name__)


def validate_server_status(server: Server, status: str):
    expected_status = ServerStatus.from_code(status)
    assert server.status == expected_status, \
        f'Server {server.id}: invalid status. ' \
        f'Actual: {server.status}, expected: {expected_status}'


# @world.run_only_if(platform='!%s' % Platform.VMWARE) <-- TODO
def validate_vcpus_info(server: Server):
    vcpus = int(server.details['info.instance_vcpus'])
    LOG.info(f'Server {server.id} vcpus info: {vcpus}')
    assert vcpus > 0, f'info.instance_vcpus not valid for {server.id}'


def validate_scalarizr_version(server: Server, branch: str = None):
    if branch == 'system' or not branch:
        branch = CONF.feature.branch
    elif branch == 'role':
        branch = CONF.feature.to_branch
    last_version = lib_agent.get_last_version(server.role.dist, branch)
    installed_version = lib_agent.get_installed_version(server)
    assert installed_version == last_version, \
        'Server does not have latest build of scalarizr package. ' \
        f'Actual: {installed_version}, expected: {last_version}'


def validate_hostname(server: Server):
    hostname = server.api.system.get_hostname().lower()
    valid_hostname = lib_server.get_hostname_by_server_format(server).lower()
    assert hostname == valid_hostname, \
        f'Hostname of server {server.id} is not valid. ' \
        f'Actual: {hostname}, expected: {valid_hostname}'


# @world.run_only_if(platform=['!%s' % Platform.RACKSPACENGUS, '!%s' % Platform.CLOUDSTACK],
#     dist=['!scientific6', '!centos-6-x', '!centos-7-x', '!coreos']) <-- TODO
def validate_iptables_ports(cloud: Cloud, server: Server, ports: List[int], invert: bool = False):
    LOG.info(f'Verify ports {ports} in iptables')
    if CONF.feature.platform.is_cloudstack:
        LOG.info('Skip iptables check for Cloudstack')
        return
    iptables_rules = lib_server.get_iptables_rules(cloud, server)
    LOG.debug(f'iptables rules:\n{iptables_rules}')
    for port in ports:
        LOG.debug(f'Check port "{port}" in iptables rules')
        if str(port) in iptables_rules and invert:
            raise AssertionError(f'Port "{port}" in iptables rules')
        elif not invert and str(port) not in iptables_rules:
            raise AssertionError(f'Port "{port}" is NOT in iptables rules')


# @world.run_only_if(platform=(Platform.EC2, Platform.GCE), storage='persistent') <-- TODO
def validate_server_message_count(context: dict, server: Server, msg: str):
    """Assert messages count with Mounted Storages count"""
    messages = lib_server.get_incoming_messages(server, msg)
    messages_count = len(messages)
    role_options = context[f'role_params_{server.farm_role_id}']
    mount_device_count = role_options.storage.volumes.count(role_options.storage)
    assert messages_count == mount_device_count, \
        f'Scalr internal messages count is wrong. ' \
        f'Actual: {messages_count}, expected: {mount_device_count}. ' \
        f'Actual messages: {messages}'
