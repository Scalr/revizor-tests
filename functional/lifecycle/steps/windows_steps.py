import time
import logging
from datetime import datetime

from lettuce import world, step

try:
    import winrm
except ImportError:
    raise ImportError("Please install WinRM")

from revizor2.conf import CONF
from revizor2.consts import Platform
from revizor2.exceptions import NotFound


LOG = logging.getLogger(__name__)


def get_windows_session(server):
    username = 'Administrator'
    port = 5985
    if CONF.feature.driver.cloud_family == Platform.GCE:
        username = 'scalr'
    elif CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        node = world.cloud.get_node(server)
        port = world.cloud.open_port(node, port)
    session = winrm.Session('http://%s:%s/wsman' % (server.public_ip, port),
                            auth=(username, server.windows_password))
    return session


def run_cmd_command(server, command):
    console = get_windows_session(server)
    LOG.info('Run command: %s in server %s' % (command, server.id))
    out = console.run_cmd(command)
    LOG.debug('Result of command: %s\n%s' % (out.std_out, out.std_err))
    if not out.status_code == 0:
        raise AssertionError('Command: "%s" exit with status code: %s and stdout: %s\n stderr:%s' % (command, out.status_code, out.std_out, out.std_err))
    return out


@step(r"file '([\w\d\:\\/_]+)' exist in ([\w\d]+) windows$")
def check_windows_file(step, path, serv_as):
    server = getattr(world, serv_as)
    out = run_cmd_command(server, 'dir %s' % path)
    if out.status_code == 0 and not out.std_err:
        return
    raise NotFound("File '%s' not exist, stdout: %s\nstderr:%s" % (path, out.std_out, out.std_err))


@step(r"I reboot windows scalarizr in ([\w\d]+)")
def reboot_windows(step, serv_as):
    server = getattr(world, serv_as)
    console = get_windows_session(server)
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
    out = run_cmd_command(server,
                          "findstr /c:\"Scalarizr terminated\" \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\"")
    if 'Scalarizr terminated' in out.std_out:
        return True
    raise AssertionError("Not see 'Scalarizr terminated' in debug log")


@step(r"not ERROR in ([\w\d]+) scalarizr windows log")
def check_errors_in_log(step, serv_as):
    server = getattr(world, serv_as)
    out = run_cmd_command(server, "findstr /c:\"ERROR\" \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\"").std_out
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


@step("last script output contains '(.+)' in (.+)$")
def assert_check_message_in_log(step, message, serv_as):
    time.sleep(60)
    server = getattr(world, serv_as)
    server.scriptlogs.reload()
    last_count = getattr(world, '%s_script_count' % serv_as)
    LOG.debug("Last count of scripts: %s" % last_count)
    scriptlogs = sorted(server.scriptlogs, key=lambda x: x.id)
    LOG.debug("Check content in logs")
    if message in scriptlogs[last_count].message:
        return True
    LOG.error("Not find content in message: %s" % scriptlogs[last_count].message)
    raise AssertionError("Not see message %s in scripts logs" % message)


@step('server ([\w\d]+) has disk with size (\d+)Gb')
def check_attached_disk_size(step, serv_as, size):
    time.sleep(60)
    size = int(size)
    server = getattr(world, serv_as)
    out = run_cmd_command(server, 'wmic logicaldisk get size,caption').std_out
    disks = filter(lambda x: x.strip(), out.splitlines()[1:])
    disks = dict([(disk.split()[0],
                   int(round(int(disk.split()[1])/1024/1024/1024.)))
                  for disk in disks])
    for disk in disks:
        if disks[disk] == size:
            return
    else:
        raise AssertionError('Any attached disk does\'nt has size "%s", all disks "%s"'
                             % (size, disks))


@step(r'I have a ([\w\d]+) attached volume as ([\w\d]+)')
def save_attached_volume_id(step, serv_as, volume_as):
    server = getattr(world, serv_as)
    attached_volume = None
    node = world.cloud.get_node(server)
    if CONF.feature.driver.current_cloud == Platform.EC2:
        volumes = server.get_volumes()
        if not volumes:
            raise AssertionError('Server %s doesn\'t has attached volumes!' %
                                 (server.id))
        attached_volume = filter(lambda x:
                                 x.extra['device'] != node.extra['root_device_name'],
                                 volumes)[0]
    elif CONF.feature.driver.current_cloud == Platform.GCE:
        volumes = filter(lambda x: x['deviceName'] != 'root',
                         node.extra.get('disks', []))
        if not volumes:
            raise AssertionError('Server %s doesn\'t has attached volumes!' %
                                 server.id)
        elif len(volumes) > 1:
            raise AssertionError('Server %s has a more 1 attached disks!' %
                                 server.id)
        attached_volume = filter(lambda x: x.name == volumes[0]['deviceName'],
                                 world.cloud.list_volumes())[0]
    elif CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        volumes = server.get_volumes()
        if len(volumes) == 1:
            raise AssertionError('Server %s doesn\'t has attached volumes!' %
                                 (server.id))
        attached_volume = filter(lambda x:
                                 x.extra['volume_type'] != 'ROOT',
                                 volumes)[0]
    setattr(world, '%s_volume' % volume_as, attached_volume)
    LOG.info('Attached volume for server "%s" is "%s"' %
             (server.id, attached_volume.id))


@step(r'attached volume ([\w\d]+) has size (\d+) Gb')
def verify_attached_volume_size(step, volume_as, size):
    LOG.info('Verify master volume has new size "%s"' % size)
    size = int(size)
    volume = getattr(world, '%s_volume' % volume_as)
    volume_size = int(volume.size)
    if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
        volume_size = volume_size/1024/1024/1024
    if not size == volume_size:
        raise AssertionError('VolumeId "%s" has size "%s" but must be "%s"'
                             % (volume.id, volume.size, size))