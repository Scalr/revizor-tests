import logging
from lettuce import world, step


LOG = logging.getLogger(__name__)


@step('I create domain ([\w\d]+) to ([\w\d]+) role')
def create_domain_to_role(step, domain_as, role_type):
    LOG.info('Create new domain for role %s as %s' % (role_type, domain_as))
    role = world.get_role(role_type)
    domain = role.create_domain()
    LOG.info('New domain: %s' % domain.name)
    setattr(world, domain_as, domain)


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
    vhost = role.add_vhost(domain.name, document_root='/var/www/%s' % vhost_as, ssl=ssl, cert=key_name)
    setattr(world, vhost_as, vhost)


@step(r'([\w]+) has (.+) in virtual hosts configuration')
def assert_check_vhost(step, serv_as, vhost_as):
    node = world.cloud.get_node(getattr(world, serv_as))
    vhost = getattr(world, vhost_as)
    out = node.run('ls /etc/scalr/private.d/vhosts/')
    if vhost.name not in out[0]:
        LOG.error('Domain %s not in vhosts, it have: %s' % (vhost.name, out))
        raise AssertionError('VHost "%s" not in apache config, in out: %s' % (vhost.name, out))
    return True


@step(r'([\w]+) has not (.+) in virtual host configuration')
def check_deleted_vhost(step, serv_as, vhost_as):
    vhost = getattr(world, vhost_as)
    node = world.cloud.get_node(getattr(world, serv_as))
    out = node.run('ls -la /etc/scalr/private.d/vhosts/%s' % vhost.name)
    for line in out[0].splitlines()+out[1].splitlines():
        if 'No such file or directory' in line:
            break
    else:
        raise AssertionError('VHost %s in apache config' % vhost.name)
    return True


@step(r'I remove from web interface virtual host (.+)')
def remove_vhost(step, vhost_as):
    LOG.info('Remove vhost %s' % vhost_as)
    vhost = getattr(world, vhost_as)
    LOG.info('Delete vhost: %s' % vhost.name)
    vhost.delete()


@step(r'I change the(?: (http|https)) virtual host (.+) template(?: (invalid))? data')
def change_vhost_template(step, proto, vhost_as, invalid=None):
    """This step is editing an existing virtual host, changing the contents of Server non-ssl template field,
    replacing their valid or not data.
    """
    #Invalid vhost templates
    invalid_template = {
        'http': """
                <VirtualHost *:xx>
                        xxServerAliasxx xxx
                        xxServerAdminxx xxx
                        xxDocumentRootxx xxx
                        xxServerNamexx xxx
                        xxCustomLogxx xxx
                        xxScriptAliasxx xxx
                </VirtualHost>""",

        'https': """
                <IfModule mod_ssl.c>
                        <VirtualHost *:443>
                                xxServerNamexx xx
                                xxServerAliasxx xx
                                xxServerAdminxx xx
                                xxDocumentRootxx xx
                                xxCustomLogxx xx
                                xxSSLEnginexx xx
                                xxSSLCertificateFilexx xx
                                xxSSLCertificateKeyFilexx xx
                                xxErrorLogxx xx
                                xxScriptAliasxx xx
                                xxSetEnvIfxx xx
                        </VirtualHost>
                </IfModule>"""
    }

    #Get VHOSTs
    vhost = getattr(world, vhost_as)
    LOG.info('Change vhost: %s, set new %s data.' % (vhost.name, 'invalid' if invalid else ''))
    #Change VHOST http template invalid data
    attribute = {'{0}_template'.format(proto): invalid_template[proto]}
    if not vhost.edit(**attribute if invalid else None):
        raise AssertionError("Can't change VHost %s in apache config" % vhost.name)
    LOG.info("VHost %s in apache config was successfully changed" % vhost.name)