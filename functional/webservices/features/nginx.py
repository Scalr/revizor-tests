import re
import urllib2
import logging
import time

from lettuce import world, step

from revizor2.cloud import Cloud
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


@step(r'bootstrap 1\+1 as \((.+), (.+)\)')
def bootstrap_two_backend(step, serv_as1, serv_as2, timeout=1400):
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


@step(r'([\w]+) upstream list should contains (.+), (.+)')
def assert_check_upstream(step, www_serv, app_serv1, app_serv2):
    time.sleep(180)
    nginx = getattr(world, www_serv)
    server1 = getattr(world, app_serv1)
    server2 = getattr(world, app_serv2)
    world.node = world.cloud.get_node(nginx)
    LOG.info('Check upstream list')
    out = world.node.run('cat /etc/nginx/app-servers.include')[0]
    if server1.private_ip in out and server2.private_ip in out:
        LOG.info('Both app server in upstream')
        return True
    LOG.error('One of the servers is not in upstream, config is: %s' % out)
    LOG.error('%s (%s) in list - %s' % (app_serv1, server1.private_ip, server1.private_ip in out))
    LOG.error('%s (%s) in list - %s' % (app_serv2, server2.private_ip, server2.private_ip in out))
    raise AssertionError('Upstreams %s or %s not in config' % (server1.private_ip, server2.private_ip))


@step(r'([\w]+) upstream list should(?: (not))? contain (.+)')
def assert_check_upstream_after_delete(step, www_serv, have, app_serv):
    server = getattr(world, app_serv)
    if have:
        LOG.info('Check if upstream not have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.node, server.private_ip, False), timeout=180, error_text="Upstream %s in list" % server.private_ip)
    else:
        LOG.info('Check if upstream have %s in list' % server.id)
        wait_until(world.wait_upstream_in_config, args=(world.node, server.private_ip), timeout=180, error_text="Upstream %s not in list" % server.private_ip)


@step(r'When I add(?: (ssl))? virtual host ([\w]+) assigned to app role')
def having_vhost(step, ssl, vhost_name):
    www_serv = getattr(world, 'W1')
    domain = www_serv.create_domain(www_serv.public_ip)
    app_serv = getattr(world, 'A1')
    if ssl:
        LOG.info('Add ssl vhost with domain: %s' % domain)
        app_serv.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=True)
    else:
        LOG.info('Add vhost with domain %s' % domain)
        app_serv.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=False)
    setattr(world, vhost_name, domain)
    LOG.debug('Update vhosts list for farm %s' % world.farm.id)
    world.farm.vhosts.reload()
    vh = None
    for vhost in world.farm.vhosts:
        LOG.debug('Vhost: %s  Domains: %s' % (vhost.name, domain))
        if vhost.name == domain:
            vh = vhost
    for role in world.farm.roles:
        if role.id == vh.farm_roleid:
            if 'app' in role.role.behaviors:
                return True
    raise AssertionError('Not have vhost to app role')


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
