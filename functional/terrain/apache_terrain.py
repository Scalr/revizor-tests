# coding: utf-8

"""
Created on 08.19.2014
@author: Eugeny Kurkovich
"""

import requests
from requests.exceptions import HTTPError, ConnectionError, SSLError
import logging
from lettuce import world, step
from revizor2.utils import wait_until
from revizor2.api import Certificate, IMPL
from revizor2.conf import CONF

LOG = logging.getLogger(__name__)

APACHE_MESSAGES = (
    'It works!',
    'Apache HTTP Server',
    'Welcome to your Scalr application',
    'Scalr farm configured succesfully',
    'Amazon Linux AMI Test Page',
    'Ok'
)


@step(r'(https|http)(?: (not))? get (.+) contains default welcome message')
def assert_check_http_get_answer(step, proto, revert, serv_as):
    server = getattr(world, serv_as)
    verify = False if proto == 'https' else None
    revert = False if not revert else True
    try:
        resp = requests.get('%s://%s' % (proto, server.public_ip), timeout=15, verify=verify)
        msg = resp.text
    except (HTTPError, ConnectionError, SSLError), e:
        if not revert:
            LOG.error('Apache error: %s' % e.message)
            raise AssertionError('Apache error: %s' % e.message)
        else:
            msg = None

    LOG.debug('Step mode: %s. Apache message: %s' % ('not contains message' if revert else 'contains message', msg))
    if not revert and not any(message in msg for message in APACHE_MESSAGES):
        raise AssertionError('Not see default message, Received message: %s,  code: %s' % (msg, resp.status_code))
    elif revert and msg:
        raise AssertionError('Error. The message in default apache https mode. Received message: %s' % msg)


@step('I add(?: (ssl))? virtual host ([\w\d]+)(?: with key ([\w\d-]+))? to ([\w\d]+) role and domain ([\w\d]+)')
def create_vhost_to_role(step, ssl, vhost_as, key_name, role_type, domain_as):
    ssl = True if ssl else False
    key_name = key_name if key_name else None
    role = world.get_role(role_type)
    domain = getattr(world, domain_as)
    LOG.info('Add new virtual host for role %s, domain %s as %s %s' % (role, domain.name, vhost_as,
                                                                       'with key {0}'.format(key_name)
                                                                       if key_name
                                                                       else ''))
    role.add_vhost(domain.name, document_root='/var/www/%s' % vhost_as, ssl=ssl, cert=key_name)
    world.farm.vhosts.reload()
    vhost = filter(lambda x: x.name == domain.name, world.farm.vhosts)[0]
    setattr(world, vhost_as, vhost)
    if not hasattr(world, 'vhosts_list'):
        setattr(world, 'vhosts_list', [])
    world.vhosts_list.append(vhost)


@step('I create domain ([\w\d]+) to ([\w\d]+) role')
def create_domain_to_role(step, domain_as, role_type):
    LOG.info('Create new domain for role %s as %s' % (role_type, domain_as))
    role = world.get_role(role_type)
    domain = role.create_domain()
    LOG.info('New domain: %s' % domain.name)
    setattr(world, domain_as, domain)


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    server = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving,
                           args=(domain.name,),
                           timeout=timeout,
                           error_text='Domain: {0} not resolve'.format(domain.name))
    assert domain_ip == server.public_ip, 'Domain IP {0} != server IP {1}'.format(
        domain_ip,
        server.public_ip)


def get_nginx_default_server_template():
    farm_settings = IMPL.farm.get_settings(world.farm.id)
    template = {
        "server": True,
        "content": farm_settings['tabParams']['nginx']['server_section'] +
                   farm_settings['tabParams']['nginx']['server_section_ssl']
    }
    return template


@step(r'([\w]+)(?: (not))? get domain ([\w\d]+)(:[\d]+)? matches ([\w\d]+) index page$')
def check_index(step, proto, revert, domain_as, port, vhost_as):
    #TODO: Rewrite this ugly
    revert = False if not revert else True
    domain = getattr(world, domain_as)
    vhost = getattr(world, vhost_as)
    domain_address = domain.name + port if port else domain.name

    if CONF.feature.platform.is_cloudstack:
        domain_server = domain.role.servers[0]
        public_port = world.cloud.open_port(
            world.cloud.get_node(domain_server),
            80 if proto == 'http' else 443
        )
        domain_address = '%s:%s' % (domain_address, str(public_port))
    # Find role by vhost
    for role in world.farm.roles:
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

    world.check_index_page(nodes, proto, revert, domain_address, vhost_as)


@step(
    r"I add (http|https|http/https) proxy (\w+)(?: with port (\d+))? to (\w+) role with ([\w\d]+) host to (\w+) role( with ip_hash)?(?: with (private|public) network)?")
def add_nginx_proxy_for_role(step, proto, proxy_name, port, proxy_role, vhost_name, backend_role, ip_hash,
                             network_type='private'):
    """This step add to nginx new proxy to any role with http/https and ip_hash
    :param proto: Has 3 states: http, https, http/https. If http/https - autoredirect will enabled
    :type proto: str
    :param proxy_name: Name for proxy in scalr interface
    :type proxy_name: str
    :param proxy_role: Nginx role name
    :type proxy_role: str
    :param backend_role: Role name for backend
    :type backend_role: str
    :param vhost_name: Virtual host name
    :type vhost_name: str
    """
    proxy_role = world.get_role(proxy_role)
    backend_role = world.get_role(backend_role)
    vhost = getattr(world, vhost_name)
    opts = {}
    port = int(port) if port else 80
    if proto == 'http':
        LOG.info('Add http proxy')
    elif proto == 'https':
        LOG.info('Add https proxy')
        opts['ssl'] = True
        opts['ssl_port'] = 443
        opts['cert_id'] = Certificate.get_by_name('revizor-key').id
        opts['http'] = True
    elif proto == 'http/https':
        LOG.info('Add http/https proxy')
        opts['ssl'] = True
        opts['ssl_port'] = 443
        opts['cert_id'] = Certificate.get_by_name('revizor-key').id
    if ip_hash:
        opts['ip_hash'] = True
    template = get_nginx_default_server_template()
    LOG.info('Add proxy to app role for domain %s' % vhost.name)
    backends = [{"farm_role_id": backend_role.id,
                 "port": "80",
                 "backup": "0",
                 "down": "0",
                 "location": "/",
                 "network": network_type}]
    proxy_role.add_nginx_proxy(vhost.name, port, templates=[template], backends=backends, **opts)
    setattr(world, '%s_proxy' % proxy_name, {"hostname": vhost.name, "port": port, "backends": backends})


