import ssl
import socket

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.consts import Platform
from revizor2.utils import wait_until
from revizor2.fixtures import resources

import logging


LOG = logging.getLogger()


# @step('([\w]+) is running on (.+)')
# def assert_check_service(step, app_name, serv_as):
#     server = (getattr(world, serv_as))
#     http_port = 80
#     if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
#         node = world.cloud.get_node(server)
#         http_port = world.cloud.open_port(node, 80, server.public_ip)
#         https_port = world.cloud.open_port(node, 443, server.public_ip)
#         world._https_port = https_port
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.settimeout(15)
#     try:
#         s.connect((server.public_ip, http_port))
#     except (socket.error, socket.timeout), e:
#         LOG.error('Service %s not work')
#         raise AssertionError(e)


@step(r'([\w]+) resolves into (.+) new ip address')
def assert_check_resolv(step, vhost_name, serv_as, timeout=1800):
    domain = getattr(world, vhost_name)
    serv = getattr(world, serv_as)
    def check_new_ip(domain, ip):
        try:
            actual_ip = wait_until(world.check_resolving, args=(domain,), timeout=timeout,
                              error_text="Not see domain resolve")
        except Exception:
            return False
        if ip == actual_ip:
            return True
        else:
            LOG.debug('Actual IP is not server IP: %s != %s' % (actual_ip, ip))
            return False
    wait_until(check_new_ip, args=(domain, serv.public_ip), timeout=timeout,
                           error_text="Domain resolve not new IP")


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, vhost_name, serv_as, timeout=1800):
    domain = getattr(world, vhost_name)
    serv = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, serv.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, serv.public_ip))


# @step(r'([\w]+) get (.+) matches (.+) index page$')
# def check_index(step, proto, vhost_name, vhost2_name):
#     domain = getattr(world, vhost_name)
#     LOG.info('Get node %s for delete index.html' % getattr(world, 'A1').id)
#     node = world.cloud.get_node(getattr(world, 'A1'))
#     try:
#         node.run('rm /var/www/%s/index.html' % vhost_name)
#     except AttributeError, e:
#         LOG.error('Failed in delete index.html: %s' % e)
#     world.check_index_page(node, proto, domain, vhost2_name)
#     world._domain = domain


@step('response contains valid Cert and CACert')
def assert_check_cert(step):
    cert = ssl.get_server_certificate((world._domain, 443))
    local_cert = resources('keys/httpd.crt').get()
    world.assert_not_equal(cert, local_cert, 'Cert not match local cert')


@after.all
def delete_vhost_domains(total):
    if not total.steps_failed and CONF.main.stop_farm:
        LOG.info("Delete vhosts and domains")
        world.farm.domains.reload()
        world.farm.vhosts.reload()
        domains = [d.id for d in world.farm.domains]
        vhosts = [v.id for v in world.farm.vhosts]
        world.farm.delete_domain(domains)
        world.farm.delete_vhost(vhosts)
