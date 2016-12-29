# coding: utf-8

"""
Created on 08.19.2014
@author: Eugeny Kurkovich
"""

import requests
from requests.exceptions import HTTPError, ConnectionError, SSLError
import logging
from lettuce import world, step

LOG = logging.getLogger(__name__)

APACHE_MESSAGES = (
    'It works!',
    'Apache HTTP Server',
    'Welcome to your Scalr application',
    'Scalr farm configured succesfully',
    'Amazon Linux AMI Test Page'
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



