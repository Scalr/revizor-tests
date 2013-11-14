import re
import logging
import time

import requests

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.consts import ServerStatus

LOG = logging.getLogger('nginx')


@step(r"http get (.+) contains '(.+)'")
def assert_check_http_get_answer(step, serv_as, mes):
    serv = getattr(world, serv_as)
    resp = requests.get('http://%s' % serv.public_ip, timeout=15).text
    if not mes in resp:
        raise AssertionError('http://%s response not contains: "%s", response: "%s"' % (serv.public_ip, mes, resp))


@step(r'bootstrap (\d+) servers as \(([\w\d, ]+)\)')
def bootstrap_many_servers(step, serv_count, serv_names, timeout=1400):
    serv_names = [s.strip() for s in serv_names.split(',')]
    role = getattr(world, world.role_type + '_role')
    for i in range(int(serv_count)):
        LOG.info('Launch %s server' % (i+1))
        role.launch_instance()
        server = world.wait_server_bootstrapping(role, ServerStatus.RUNNING, timeout=timeout)
        LOG.info('Server %s bootstrapping as %s' % (server.id, serv_names[i]))
        setattr(world, serv_names[i], server)


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
        server = getattr(world, serv)
        LOG.info('Validate server %s in upstream list' % server.id)
        if not server.private_ip in out:
            raise AssertionError('Private IP from server %s not found in upstream' % server.id)


@step(r'([\w]+) upstream list should(?: (not))? contain (.+)')
def assert_check_upstream_after_delete(step, www_serv, have, app_serv):
    server = getattr(world, app_serv)
    www_serv = getattr(world, www_serv)
    if have:
        LOG.info('Check if upstream not have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), server.private_ip, False),
                   timeout=180, error_text="Upstream %s in list" % server.private_ip)
    else:
        LOG.info('Check if upstream have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), server.private_ip),
                   timeout=180, error_text="Upstream %s not in list" % server.private_ip)


@step(r'my IP in ([\w]+) ([\w]+)([ \w]+)? access logs$')
def check_rpaf(step, serv_as, domain_as, ssl=None):
    LOG.debug('Check mod_rpaf')
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    domain = getattr(world, domain_as)
    path = '/var/log/http-%s-access.log' % domain.name
    LOG.info('Check my IP in %s log' % path)
    out = node.run('cat %s' % path)
    LOG.debug('Access log (%s) contains: %s' % (path, out[0]))
    page = urllib2.urlopen('http://www.showmemyip.com/').read()
    ip = re.findall('((?:[\d]+)\.(?:[\d]+)\.(?:[\d]+)\.(?:[\d]+))', page)[0]
    LOG.info('My public IP is %s' % ip)
    if not ip in out[0]:
        raise AssertionError('Not see my IP in access log')


@step(r'I add (\w+) role as app role in ([\w\d]+) scalarizr config')
def add_custom_role_to_backend(step, role, serv_as):
    LOG.info("Add %s role to %s scalarizr config" % (role, serv_as))
    server = getattr(world, serv_as)
    role = getattr(world, '%s_role' % role)
    node = world.cloud.get_node(server)
    node.run("sed -i 's/upstream_app_role =/upstream_app_role = %s/g' /etc/scalr/public.d/www.ini" % role.name)


@step(r'I remove (\w+) role from ([\w\d]+) scalarizr config')
def delete_custom_role_from_backend(step, role, serv_as):
    LOG.info("Delete %s role to %s scalarizr config" % (role, serv_as))
    server = getattr(world, serv_as)
    role = getattr(world, '%s_role' % role)
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