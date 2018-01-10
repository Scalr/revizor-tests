import time
import logging
import re
from datetime import datetime

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Platform
from revizor2.exceptions import NotFound


LOG = logging.getLogger(__name__)


@step(r"file '([\w\d\:\\/_-]+)' exist in ([\w\d]+) windows$")
def check_windows_file(step, path, serv_as):
    server = getattr(world, serv_as)
    for _ in range(3):
        out = world.run_cmd_command(server, 'type %s' % path)
        if out.status_code == 0 and not out.std_err:
            return
        time.sleep(10)
    raise NotFound("File '%s' not exist, stdout: %s\nstderr:%s" % (path, out.std_out, out.std_err))


@step(r"I reboot windows scalarizr in ([\w\d]+)")
def reboot_windows(step, serv_as):
    server = getattr(world, serv_as)
    console = world.get_windows_session(server)
    LOG.info('Restart scalarizr via winrm')
    LOG.debug('Stop scalarizr')
    out = console.run_cmd('net stop Scalarizr')
    time.sleep(3)
    LOG.debug(out)
    out = console.run_cmd('net start Scalarizr')
    LOG.debug(out)
    time.sleep(15)


@step(r"see 'Scalarizr terminated' in ([\w\d]+) windows log")
def check_terminated_in_log(step, serv_as):
    server = getattr(world, serv_as)
    if CONF.feature.ci_repo == 'buildbot':
        out = world.run_cmd_command(server,
                              "findstr /c:\"Scalarizr terminated\" \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\"")
    else:
        out = world.run_cmd_command(server,
                              "findstr /c:\"Scalarizr terminated\" \"C:\opt\scalarizr\\var\log\scalarizr_debug.log\"")
    if 'Scalarizr terminated' in out.std_out:
        return True
    raise AssertionError("Not see 'Scalarizr terminated' in debug log")


@step(r"not ERROR in ([\w\d]+) scalarizr windows log")
def check_errors_in_log(step, serv_as):
    server = getattr(world, serv_as)
    out = world.run_cmd_command(server,
                                "findstr /c:\"ERROR\" \"C:\\opt\\scalarizr\\var\\log\\scalarizr_debug.log\"",
                                raise_exc=False).std_out
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


@step(r"server ([\w\d]+) has disks ([((?:\w):(?:\\\w+)?)(?:\(\w+_label\d*\))? (\d+) Gb,]+)")
@world.run_only_if(platform=(Platform.EC2, Platform.GCE))
def check_attached_disk_size(step, serv_as, disks):
    server = getattr(world, serv_as)
    cdisks = re.findall(r'([\w\d\:\\]+)(\([\w\d_]+\))? (\d+) Gb', disks)
    out = world.run_cmd_command(server, 'wmic volume get Caption,Capacity,Label').std_out
    server_disks = [line.split() for line in out.splitlines() if line.strip()][1:]
    for d, label, size in cdisks:
        for disk in server_disks:
            if disk[1] == d:
                ssize = (int(disk[0]) / 1000000000)
                if ssize != int(size):
                    raise AssertionError("Disk %s is of wrong size  - %s " % (disk[1], ssize))
                if len(disk) > 2 and disk[2] not in label:
                    raise AssertionError("Disk %s has an incorrect or no label %s. Should be %s." % (
                        disk[1], disk[2], label))
                break
        else:
            raise AssertionError("Disk not found! All server disks %s " % (server_disks))


@step(r"I remove file '([\w\W]+)' from ([\w\d]+) windows")
def remove_file(step, file_name, serv_as):
    server = getattr(world, serv_as)
    cmd = 'del /F %s' % file_name
    res = world.run_cmd_command(server, cmd)
    assert not res.std_err, "An error occurred while try to delete %s:\n%s" % (file_name, res.std_err)


@step(r"I check file '([\w\W]+)' ([\w\W]+)*exist on ([\w\d]+) windows")
def check_file_exist(step, file_name, negation, serv_as):
    server = getattr(world, serv_as)
    cmd = "if {negation}exist {file_name} ( echo succeeded ) else echo failed 1>&2".format(
        negation = negation or '',
        file_name = file_name)
    res = world.run_cmd_command(server, cmd)
    assert res.std_out, '%s is %sexist on %s' % (file_name, negation or '', server.id)
