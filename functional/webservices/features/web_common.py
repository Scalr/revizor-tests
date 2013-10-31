import ssl

from lettuce import world, step, after

import requests

from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.fixtures import resources

import logging


LOG = logging.getLogger('web-common')


@step(r'([\w]+) resolves into (.+) new ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    serv = getattr(world, serv_as)

    def check_new_ip(domain_name, ip):
        try:
            actual_ip = wait_until(world.check_resolving, args=(domain_name,), timeout=timeout,
                              error_text="Not see domain resolve")
        except Exception:
            return False
        if ip == actual_ip:
            return True
        else:
            LOG.debug('Actual IP is not server IP: %s != %s' % (actual_ip, ip))
            return False
    wait_until(check_new_ip, args=(domain.name, serv.public_ip), timeout=timeout,
                           error_text="Domain resolve not new IP")


@step(r'([\w]+) get domain ([\w\d]+) matches ([\w\d]+) index page$')
def check_index(step, proto, domain_as, vhost_as):
    domain = getattr(world, domain_as)
    vhost = getattr(world, vhost_as)

    for role in world.farm.roles: # Find role by vhost
        if role.id == vhost.farm_roleid:
            app_role = role
            break
    else:
        raise AssertionError('Can\'t find role for vhost %s' % vhost.id)

    nodes = []
    app_role.servers.reload()
    for s in app_role.servers: # delete pre-defined index.html file and upload vhost file
        if not s.status == 'Running':
            continue
        node = world.cloud.get_node(s)
        nodes.append(node)
        try:
            LOG.info('Delete %s/index.html in server %s' % (vhost_as, s.id))
            node.run('rm /var/www/%s/index.html' % vhost_as)
        except AttributeError, e:
            LOG.error('Failed in delete index.html: %s' % e)

    world.check_index_page(nodes, proto, domain.name, vhost_as)


@step(r'([\w]+) get domain ([\w\d]+) matches \'(.+)\'$')
def check_matches_in_domain(step, proto, domain_as, matched_text):
    domain = getattr(world, domain_as)
    LOG.info('Match text %s in domain %s' % (matched_text, domain.name))

    if proto.isdigit():
        url = 'http://%s:%s/' % (domain.name, proto)
    else:
        url = '%s://%s/' % (proto, domain.name)
    LOG.info('Try open url: %s' % url)
    resp = requests.get(url).text
    if not resp == matched_text:
        raise AssertionError('Text "%s" not matched with "%s"' % (resp, matched_text))


@step('I start BaseHttpServer on (\d+) port in ([\w\d]+)$')
def start_basehttpserver(step, port, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Run BaseHttpServer in server %s' % server.id)

    node = world.cloud.get_node(server)
    LOG.debug('Put base_server.py script')
    node.put_file('/tmp/base_server.py', resources('scripts/base_server.py').get())
    LOG.debug('Run BaseHttpServer script')
    if node.os[0] in ['ubuntu', 'debian']:
        node.run('apt-get install screen -y')
    elif node.os[0] in ['centos', 'redhat', 'oel']:
        node.run('yum install screen -y')
    node.run('iptables -A INPUT -p tcp --dport %s -j ACCEPT' % port)
    node.run('screen -d -m python /tmp/base_server.py %s' % port)


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    serv = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain.name,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, serv.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, serv.public_ip))


@step('domain ([\w\d]+) contains valid Cert and CACert')
def assert_check_cert(step, domain_as):
    domain = getattr(world, domain_as)
    cert = ssl.get_server_certificate((domain.name, 443))
    local_cert = resources('keys/httpd.crt').get()
    world.assert_not_equal(cert, local_cert, 'Cert not match local cert')