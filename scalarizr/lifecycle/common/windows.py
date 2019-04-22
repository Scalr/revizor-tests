import logging
import time
import typing as tp
from datetime import datetime

from revizor2 import CONF
from revizor2.api import Server
from revizor2.cloud import Cloud

LOG = logging.getLogger(__name__)


def assert_attached_disks_size(cloud: Cloud, server: Server, disks: tp.List[tp.Tuple[str, str, int]]):
    node = cloud.get_node(server)
    out = node.run('wmic volume get Caption,Capacity,Label').std_out
    server_disks = [line.split() for line in out.splitlines() if line.strip()][1:]
    for d, label, size in disks:
        for disk in server_disks:
            if disk[1] == d:
                server_size = int(disk[0]) // 1000000000
                if server_size != size:
                    raise AssertionError("Disk %s is of wrong size  - %s " % (disk[1], server_size))
                if len(disk) > 2 and disk[2] not in label:
                    raise AssertionError("Disk %s has incorrect or no label '%s'. Should be '%s'." % (
                        disk[1], disk[2], label))
                break
        else:
            raise AssertionError("Disk not found! All server disks %s" % server_disks)


def agent_restart(cloud: Cloud, server: Server):
    # TODO: PP > consolidate win/linux methods
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        LOG.info('Restart scalarizr via winrm')
        LOG.debug('Stop scalarizr')
        out = conn.run('net stop Scalarizr')
        time.sleep(3)
        LOG.debug(out)
        out = conn.run('net start Scalarizr')
        LOG.debug(out)
        time.sleep(15)


def assert_szr_terminated_in_log(cloud: Cloud, server: Server):
    # TODO: PP > consolidate win/linux methods
    node = cloud.get_node(server)
    if CONF.feature.ci_repo == 'buildbot':
        out = node.run("findstr /c:\"Scalarizr terminated\" \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\"")
    else:
        out = node.run("findstr /c:\"Scalarizr terminated\" \"C:\opt\scalarizr\\var\log\scalarizr_debug.log\"")
    if 'Scalarizr terminated' in out.std_out:
        return True
    raise AssertionError("Not see 'Scalarizr terminated' in debug log")


def assert_errors_in_szr_logs(cloud: Cloud, server: Server):
    node = cloud.get_node(server)
    out = node.run("findstr /c:\"ERROR\" \"C:\\opt\\scalarizr\\var\\log\\scalarizr_debug.log\"").std_out
    errors = []
    if 'ERROR' in out:
        log = out.splitlines()
        for l in log:
            try:
                d = datetime.strptime(l.split()[0], '%Y-%m-%d')
                log_level = l.strip().split()[3]
            except ValueError:
                continue
            now = datetime.now()
            if not d.year == now.year or not d.month == now.month or not d.day == now.day or not log_level == 'ERROR':
                continue
            errors.append(l)
    if errors:
        raise AssertionError('ERROR in log: %s' % errors)
