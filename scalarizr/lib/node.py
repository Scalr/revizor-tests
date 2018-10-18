import logging
import time

from revizor2 import CONF
from revizor2.api import Cloud, Server
from revizor2.utils import wait_until
import scalarizr.lib.server as lib_server

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
