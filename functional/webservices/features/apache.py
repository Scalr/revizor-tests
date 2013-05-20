import urllib2
import logging

from lettuce import world, step

LOG = logging.getLogger('apache')


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


@step(r'I add(?: (ssl))? virtual host ([\w]+) to ([\w]+)')
def add_vhost(step, ssl, vhost_name, serv_as):
    serv = getattr(world, serv_as)
    domain = serv.create_domain()
    if ssl:
        LOG.info('Add SSL vhost with domain %s' % domain)
        serv.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=True)
    else:
        LOG.info('Add vhost with domain %s' % domain)
        serv.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl=False)
    setattr(world, vhost_name, domain)
    LOG.info('Domain %s (%s) has been added to %s server' % (domain, vhost_name, serv.id))


@step(r'([\w]+) has (.+) in virtual hosts configuration')
def assert_check_vhost(step, serv_as, vhost_name):
    node = world.cloud.get_node(getattr(world, serv_as))
    domain = getattr(world, vhost_name)
    out = node.run('ls /etc/scalr/private.d/vhosts/')[0]
    if domain in out:
        return True
    LOG.error('Domain %s not in vhosts, it have: %s' % (domain, out))
    raise AssertionError('VHost not in apache config, in out: %s' % out)


@step(r'Given I have virtual host (.+) assigned to app role')
def having_vhost(step, vhost_name):
    domain = getattr(world, vhost_name)
    LOG.debug('Give domain: %s' % domain)
    world.farm.vhosts.reload()
    vh = None
    for vhost in world.farm.vhosts:
        LOG.debug('Vhost: %s' % vhost.name)
        if vhost.name == domain:
            LOG.info('Find vhost with domain %s' % domain)
            vh = vhost
    for role in world.farm.roles:
        if role.id == vh.farm_roleid:
            if 'app' in role.role.behaviors:
                return True
    LOG.error('Vhost %s is not assigned to app role' % domain)
    raise AssertionError('Not have vhost to app role')


@step(r'I remove virtual host (.+)')
def remove_vhost(step, vhost_name):
    LOG.info('Remove vhost %s' % vhost_name)
    domain = getattr(world, vhost_name)
    for vhost in world.farm.vhosts:
        if vhost.name == domain:
            LOG.info('Delete vhost: %s' % domain)
            vhost.delete()


@step(r'([\w]+) has no (.+) in virtual host configuration')
def check_deleted_vhost(step, serv_as, vhost_name):
    domain = getattr(world, vhost_name)
    node = world.cloud.get_node(getattr(world, serv_as))
    out = node.run('ls -la /etc/scalr/private.d/vhosts/%s' % domain)
    for line in out[0].splitlines()+out[1].splitlines():
        if 'No such file or directory' in line:
            return True
    raise AssertionError('VHost in apache config')
