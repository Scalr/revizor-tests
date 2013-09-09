import os
import time
import logging
from datetime import datetime

from lettuce import world, step
try:
    from winrm import winrm_service, exceptions as winrm_exceptions
except ImportError:
    print "Please install WinRM"

from revizor2.api import Farm, IMPL
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.consts import ServerStatus, Platform

LOG = logging.getLogger('lifecycle-windows')


@step(r"file '([\w\d\:\\/_]+)' exist in ([\w\d]+)")
def check_windows_file(step, path, serv_as):
    server = getattr(world, serv_as)
    console = winrm_service.WinRMWebService(endpoint='http://%s:5985/wsman' % server.public_ip, username="Administrator",
                                            password=server.ec2_windows_password, transport="plaintext")
    LOG.debug('Open windows shell')
    for i in range(10):
        try:
            LOG.debug("Try open shell")
            shell_id = console.open_shell()
            break
        except winrm_exceptions.WinRMTransportError:
            time.sleep(30)
    LOG.info('Run command: %s' % 'ls %s' % path)
    com_id = console.run_command(shell_id, 'ls %s' % path)
    out = console.get_command_output(shell_id, com_id)
    LOG.debug('Result of command:')
    LOG.debug(out)
    if path in out[0]:
        return
    raise AssertionError("Not found: %s, out: %s" % (path, out))


@step(r"I reboot windows scalarizr in ([\w\d]+)")
def reboot_windows(step, serv_as):
    server = getattr(world, serv_as)
    console = winrm_service.WinRMWebService(endpoint='http://%s:5985/wsman' % server.public_ip, username="Administrator",
                                            password=server.ec2_windows_password, transport="plaintext")
    LOG.debug('Open windows shell')
    shell_id = console.open_shell()
    LOG.info('Restart scalarizr via winrm')
    com_id = console.run_command(shell_id, 'net stop Scalarizr')
    out = console.get_command_output(shell_id, com_id)
    com_id = console.run_command(shell_id, 'net start Scalarizr')
    out = console.get_command_output(shell_id, com_id)
    LOG.debug('Result of command:')
    LOG.debug(out)
    time.sleep(15)


@step(r"see 'Scalarizr terminated' in ([\w\d]+) windows log")
def check_terminated_in_log(step, serv_as):
    server = getattr(world, serv_as)
    console = winrm_service.WinRMWebService(endpoint='http://%s:5985/wsman' % server.public_ip, username="Administrator",
                                            password=server.ec2_windows_password, transport="plaintext")
    LOG.debug('Open windows shell')
    shell_id = console.open_shell()
    #TODO: Add path
    LOG.info("Run command: cat \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\" | grep 'Scalarizr terminated'")
    com_id = console.run_command(shell_id, "cat \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\" | grep 'Scalarizr terminated'")
    out = console.get_command_output(shell_id, com_id)
    LOG.debug('Result of command:')
    LOG.debug(out)
    if 'Scalarizr terminated' in out[0]:
        return True
    raise AssertionError("Not see 'Scalarizr terminated' in debug log")


@step(r"not ERROR in ([\w\d]+) scalarizr windows log")
def check_errors_in_log(step, serv_as):
    server = getattr(world, serv_as)
    console = winrm_service.WinRMWebService(endpoint='http://%s:5985/wsman' % server.public_ip, username="Administrator",
                                            password=server.ec2_windows_password, transport="plaintext")
    LOG.debug('Open windows shell')
    shell_id = console.open_shell()
    #TODO: Add path
    LOG.info("Run command cat \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\" | grep ERROR")
    com_id = console.run_command(shell_id, "cat \"C:\Program Files\Scalarizr\\var\log\scalarizr_debug.log\" | grep ERROR")
    out = console.get_command_output(shell_id, com_id)
    LOG.debug('Result of command:')
    LOG.debug(out)
    errors = []
    out = out[0]
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