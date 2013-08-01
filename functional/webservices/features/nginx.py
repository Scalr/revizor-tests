import re
import urllib2
import logging
import time

from lettuce import world, step

from revizor2.utils import wait_until


LOG = logging.getLogger('nginx')


@step(r"http get (.+) contains '(.+)'")
def assert_check_http_get_answer(step, serv_as, mes):
    serv = getattr(world, serv_as)
    req = urllib2.urlopen('http://%s' % serv.public_ip, timeout=15)
    if req.code == 200:
        msg = req.read()
        if not mes.strip() in msg.strip():
            raise AssertionError('Not see message: %s, see: %s' % (mes, msg))
        LOG.info('Server %s http response contain %s' % (serv.id, mes))
    else:
        raise AssertionError('Not standart answer, code: %s' % req.code)


@step(r'bootstrap 2 servers as \((.+), (.+)\)')
def bootstrap_two_backend(step, serv_as1, serv_as2, timeout=1400):
    #TODO: Fix pre-defined 2 servers
    spec = 'running'
    role = getattr(world, world.role_type + '_role')
    LOG.info('Bootstrap first server')
    server = wait_until(world.check_server_status, args=(spec, role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    setattr(world, serv_as1, server)
    LOG.info('First server is %s' % server.id)
    LOG.info('Launch second server')
    role.launch_instance()
    LOG.info('Bootstrap second server')
    server = wait_until(world.check_server_status, args=(spec, role.role_id), timeout=timeout, error_text="I'm not see this %s state in server" % spec)
    setattr(world, serv_as2, server)
    LOG.info('Second server is %s' % server.id)


@step(r'([\w]+) upstream list should contains (.+)$')
def assert_check_upstream(step, www_serv, app_servers):
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
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), server.private_ip, False), timeout=180, error_text="Upstream %s in list" % server.private_ip)
    else:
        LOG.info('Check if upstream have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.cloud.get_node(www_serv), server.private_ip), timeout=180, error_text="Upstream %s not in list" % server.private_ip)


@step(r'I add(?: (ssl))? virtual host ([\w]+) assigned to ([\w\d]+) role')
def having_vhost(step, ssl, vhost_name, role_name):
    www_serv = getattr(world, 'W1')
    domain = www_serv.create_domain(www_serv.public_ip)
    role = getattr(world, '%s_role' % role_name)
    if ssl:
        LOG.info('Add ssl vhost with domain: %s' % domain)
        role.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=True)
    else:
        LOG.info('Add vhost with domain %s' % domain)
        role.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=False)
    setattr(world, vhost_name, domain)
    LOG.debug('Update vhosts list for farm %s' % world.farm.id)
    world.farm.vhosts.reload()
    time.sleep(10)
    #TODO: Check this
    # vh = None
    # for vhost in world.farm.vhosts:
    #     LOG.debug('Vhost: %s  Domains: %s' % (vhost.name, domain))
    #     if vhost.name == domain:
    #         vh = vhost
    # for role in world.farm.roles:
    #     if role.id == vh.farm_roleid:
    #         if 'app' in role.role.behaviors:
    #             return True
    # raise AssertionError('Not have vhost to app role')


@step(r'my IP in ([\w]+) ([\w]+)([ \w]+)? access logs$')
def check_rpaf(step, serv_as, vhost_name, ssl=None):
    LOG.debug('Check mod_rpaf')
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    domain = getattr(world, vhost_name)
    path = '/var/log/http-%s-access.log' % domain
    LOG.info('Check my IP in %s log' % path)
    out = node.run('cat %s' % path)
    LOG.debug('Access log (%s) contains: %s' % (path, out[0]))
    page = urllib2.urlopen('http://www.showmemyip.com/').read()
    ip = re.findall('((?:[\d]+)\.(?:[\d]+)\.(?:[\d]+)\.(?:[\d]+))', page)[0]
    LOG.info('My public IP is %s' % ip)
    if not ip in out[0]:
        raise AssertionError('Not see my IP in access log')
