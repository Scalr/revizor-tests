import urllib2
import logging

from lettuce import world, step

LOG = logging.getLogger('apache')


@step('I create domain ([\w\d]+) to ([\w\d]+) role')
def create_domain_to_role(step, domain_as, role):
    LOG.info('Create new domain for role %s as %s' % (role, domain_as))
    role = getattr(world, '%s_role' % role)
    domain = role.create_domain()
    LOG.info('New domain: %s' % domain.name)
    setattr(world, domain_as, domain)


@step('I add(?: (ssl))? virtual host ([\w\d]+) to ([\w\d]+) role and domain ([\w\d]+)')
def create_vhost_to_role(step, ssl, vhost_as, role, domain_as):
    ssl = True if ssl else False
    role = getattr(world, '%s_role' % role)
    domain = getattr(world, domain_as)
    LOG.info('Add new virtual host for role %s, domain %s as %s' % (role, domain.name, vhost_as))
    vhost = role.add_vhost(domain.name, document_root='/var/www/%s' % vhost_as, ssl=ssl)
    setattr(world, vhost_as, vhost)


@step(r'http get (.+) contains default welcome message')
def assert_check_http_get_answer(step, serv_as):
    serv = getattr(world, serv_as)
    try:
        req = urllib2.urlopen('http://%s' % serv.public_ip, timeout=15)
        msg = req.read()
        code = req.code
    except urllib2.HTTPError, e:
        msg = e.read()
        code = e.code
    LOG.debug('Apache message: %s' % msg)
    if 'It works!' in msg or 'Apache HTTP Server' in msg or 'Welcome to your Scalr application' in msg:
        return True
    else:
        raise AssertionError('Not see default message, code: %s' % code)


@step(r'([\w]+) has (.+) in virtual hosts configuration')
def assert_check_vhost(step, serv_as, vhost_as):
    node = world.cloud.get_node(getattr(world, serv_as))
    vhost = getattr(world, vhost_as)
    out = node.run('ls /etc/scalr/private.d/vhosts/')[0]
    if vhost.name in out:
        return True
    LOG.error('Domain %s not in vhosts, it have: %s' % (vhost.name, out))
    raise AssertionError('VHost not in apache config, in out: %s' % out)


@step(r'([\w]+) has not (.+) in virtual host configuration')
def check_deleted_vhost(step, serv_as, vhost_as):
    vhost = getattr(world, vhost_as)
    node = world.cloud.get_node(getattr(world, serv_as))
    out = node.run('ls -la /etc/scalr/private.d/vhosts/%s' % vhost.name)
    for line in out[0].splitlines()+out[1].splitlines():
        if 'No such file or directory' in line:
            return True
    raise AssertionError('VHost %s in apache config' % vhost.name)


@step(r'I remove virtual host (.+)')
def remove_vhost(step, vhost_as):
    LOG.info('Remove vhost %s' % vhost_as)
    vhost = getattr(world, vhost_as)
    LOG.info('Delete vhost: %s' % vhost.name)
    vhost.delete()

