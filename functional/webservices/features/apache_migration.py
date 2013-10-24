__author__ = 'gigimon'

import urllib2
import logging

from lettuce import world, step

LOG = logging.getLogger('apache-migration')


@step('I create domain ([\w\d])+ to ([\w\d]+) role')
def create_domain_to_role(step, domain_as, role):
    LOG.info('Create new domain for role %s as %s' % (role, domain_as))
    role = getattr(world, '%s_role' % role)
    domain = role.create_domain()
    LOG.info('New domain: %s' % domain.name)
    setattr(world, '%s_domain' % domain_as, domain)


@step('I add(?: (ssl))? virtual host ([\w\d]+) to ([\w\d]+) role and domain ([\w\d]+)')
def create_vhost_to_role(step, ssl, vhost_as, role, domain_as):
    ssl = True if ssl.strip() else False
    role = getattr(world, '%s_role' % role)
    domain = getattr(world, '%s_domain' % domain_as)
    LOG.info('Add new virtual host for role %s, domain %s as %s' % (role, domain.name, vhost_as))
    vhost = role.add_vhost(domain.name, document_root='/var/www/%s' % vhost_as, ssl=ssl)
    setattr(world, '%s_vhost' % vhost_as, vhost)