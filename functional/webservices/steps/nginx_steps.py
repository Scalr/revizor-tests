import re
import time
import logging

import requests

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.consts import ServerStatus


LOG = logging.getLogger(__name__)


@step(r"http get (.+) contains default message")
def assert_check_http_get_answer(step, serv_as):
    #TODO: Move to common with apache
    server = getattr(world, serv_as)
    nginx_mes = ['No running app instances found',
           'Backend server did not respond in time',
           'the Amazon Linux AMI',
           'Welcome to <strong>nginx</strong> on EPEL!']
    resp = requests.get('http://%s' % server.public_ip, timeout=120).text
    if not any(message in resp for message in nginx_mes):
        raise AssertionError('http://%s response not contains: "%s", Response is: "%s"' % (server.public_ip, nginx_mes, resp))


@step(r'([\w]+) upstream list should contains (.+)$')
def assert_check_upstream(step, www_serv, app_servers):
    LOG.info('Check app servers %s in app-servers.include')
    time.sleep(180)
    nginx = getattr(world, www_serv)
    node = world.cloud.get_node(nginx)
    out = node.run('cat /etc/nginx/app-servers.include')[0]
    app_servers = [s.strip() for s in app_servers.split(',')]
    LOG.info('Check upstream list')
    for serv in app_servers:
        network_type = 'private'
        if ':' in serv:
            serv_as, network_type = serv.split(':')
        else:
            serv_as = serv
        server = getattr(world, serv_as)
        LOG.info('Validate server %s in upstream list' % server.id)
        server_ip = getattr(server, '%s_ip' % network_type)
        if not server_ip in out:
            raise AssertionError('IP address %s from server %s not found in upstream' % (server_ip, server.id))


@step(r'([\w]+) upstream list should(?: (not))? contain ([\w\d]+)( remembered private_ip)?')
def assert_check_upstream_after_delete(step, www_serv, have, app_serv, private_ip=None):
    server = getattr(world, app_serv)
    www_serv = getattr(world, www_serv)
    ip = getattr(world, '%s_private_ip' % app_serv) if private_ip else server.private_ip
    if have:
        LOG.info('Check if upstream not have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), ip, False),
                   timeout=180, error_text="Server %s (%s) in upstream list" % (server.id, ip))
    else:
        LOG.info('Check if upstream have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), ip),
                   timeout=180, error_text="Server %s (%s) not in upstream list" % (server.id, ip))


@step(r'I have remembered private_ip of ([\w\d]+)')
def save_server_public_ip(step, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Save public_ip (%s) of server %s' % (server.private_ip, server.id))
    setattr(world, '%s_private_ip' % serv_as, server.private_ip)


@step(r'I add (\w+) role as app role in ([\w\d]+) scalarizr config')
def add_custom_role_to_backend(step, role_type, serv_as):
    LOG.info("Add %s role to %s scalarizr config" % (role_type, serv_as))
    server = getattr(world, serv_as)
    role = world.get_role(role_type)
    node = world.cloud.get_node(server)
    node.run("sed -i 's/upstream_app_role =/upstream_app_role = %s/g' /etc/scalr/public.d/www.ini" % role.name)


@step(r'I remove (\w+) role from ([\w\d]+) scalarizr config')
def delete_custom_role_from_backend(step, role_type, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Delete %s role from %s scalarizr config' % (role_type, server.id))
    role = world.get_role(role_type)
    node = world.cloud.get_node(server)
    node.run("sed -i 's/upstream_app_role = %s/upstream_app_role =/g' /etc/scalr/public.d/www.ini" % role.name)


@step(r'([\w\d]+) upstream list should be default')
def app_server_should_be_clean(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    out = node.run('cat /etc/nginx/app-servers.include')[0]
    ips = re.findall(r"((?:\d+\.?){4}:\d+)", out)
    if not len(ips) == 1:
        raise AssertionError('In default app-servers.include must be only one host, but it: %s (%s)' % (len(ips), ips))
    if not ips[0] == '127.0.0.1:80':
        raise AssertionError('First host in default app-server.include is not localhost, it: %s' % ips)