import time
import logging
from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Platform


LOG = logging.getLogger(__name__)


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
    # if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
    #     LOG.debug('Wait 8 minutes in cloudstack')
    #     time.sleep(500)


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