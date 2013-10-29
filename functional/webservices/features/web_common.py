import ssl

from lettuce import world, step, after

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