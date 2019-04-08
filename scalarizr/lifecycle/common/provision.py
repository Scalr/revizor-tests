import logging

import chef

from revizor2 import api
from revizor2.conf import CONF
from revizor2.consts import Dist
from revizor2.utils import wait_until
from revizor2.cloud import Cloud, ExtendedNode

from scalarizr.lib import server as lib_server
from scalarizr.lib import farm as lib_farm


LOG = logging.getLogger(__name__)


def get_chef_bootstrap_stat(node: ExtendedNode):
    # Get chef client.pem update time
    bootstrap_stat = node.run('stat -c %Y /etc/chef/client.pem').std_out.split()[0]
    LOG.debug(f'Chef client.pem, last modification time: {bootstrap_stat}')
    return bootstrap_stat


def check_process_options(node: ExtendedNode, process: str, options: str):
    # TODO: Add systemd support
    LOG.debug(f'Want check process {process} and options {options}')
    with node.remote_connection() as conn:
        for _ in range(3):
            out = conn.run('ps aux | grep %s' % process)
            LOG.debug('Grep for ps aux: %s' % out.std_out)
            for line in out.std_out.splitlines():
                if 'grep' in line:
                    continue
                LOG.info('Work with line: %s' % line)
                if options not in line and not CONF.feature.dist == Dist(
                        'amzn1609') and not CONF.feature.dist.is_systemd:
                    raise AssertionError('Options %s not in process, %s' % (options, ' '.join(line.split()[10:])))
                else:
                    return True
        raise AssertionError(f'Not found process: {process}')


def check_process_status(node: ExtendedNode, process: str, work: bool = False):
    LOG.info(f"Check running process {process} on server")
    list_proc = node.run('ps aux | grep %s' % process).std_out.split('\n')
    processes = filter(lambda x: 'grep' not in x and x, list_proc)
    msg = f"Process {process} on server {node.id} not in valid state"
    assert not processes if work else processes, msg


def verify_chef_hostname(cloud: Cloud, server: api.Server):
    node = cloud.get_node(server)
    cmd = 'findstr node_name c:\\chef\\client.rb' if CONF.feature.dist.is_windows \
        else 'cat /etc/chef/client.rb | grep node_name'
    node_name = node.run(cmd).std_out
    node_name = node_name.strip().split()[1][1:-1]
    hostname = lib_server.get_hostname_by_server_format(server)
    if not node_name == hostname:
        raise AssertionError(f'Chef node_name "{node_name}" != hostname on server "{hostname}"')


def check_node_exists_on_chef_server(server: api.Server, exist: bool = True):
    hostname = lib_server.get_hostname_by_server_format(server)
    LOG.debug(f'Chef node name: {hostname}')

    chef_api = chef.autoconfigure()

    if not isinstance(chef_api, chef.api.ChefAPI):
        raise AssertionError("Can't initialize ChefAPI instance.")

    node = chef.Node(hostname, api=chef_api)

    if node.exists != exist:
        raise AssertionError(f'Server {server.id} with hostname {hostname} in state {node.exists} '
                             f'on Chef server but need: {exist}')


def wait_for_farm_state(farm: api.Farm, state):
    """Wait for state of farm"""
    wait_until(lib_farm.get_farm_state, args=(farm, state),
               timeout=300, error_text=f'Farm not in status {state}')


def check_file_exist_on_win(node: ExtendedNode, filename: str, exist: bool = True):
    #TODO: Make universal method
    cmd = f"if exist {filename} ( echo succeeded ) else echo failed"
    res = node.run(cmd).std_out
    file_exist = 'succeeded' in res
    assert exist == file_exist, f'File {filename} exist={file_exist} in server but must {exist}'


def remove_file_on_win(node: ExtendedNode, filename: str):
    cmd = f'del /F {filename}'
    res = node.run(cmd)
    assert not res.std_err, f"An error occurred while try to delete {filename}:\n{res.std_err}"
