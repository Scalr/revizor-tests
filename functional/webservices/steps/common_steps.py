import ssl
import logging
from socket import socket

from lettuce import world, step

import requests

import OpenSSL
from OpenSSL.SSL import TLSv1_METHOD, Context, Connection
from OpenSSL.crypto import FILETYPE_PEM

from revizor2.utils import wait_until
from revizor2.fixtures import resources


LOG = logging.getLogger(__name__)


#Uses for supporting TLS SNI
class OpenSSLSNI(object):
    """This class implements the functionality of obtaining certificates secure connection using
        apache TLS Extension Server Name Indication (SNI)
    """
    def connection(func):
        def wrapped(self):
            self._connect()
            try:
                return func(self)
            finally:
                self._close()
        return wrapped

    def __init__(self, host, port):
        #Set host name
        self._host = str(host).split('//')[-1].split(':')[0]
        #Set port
        self._port = int(port) if str(port).isdigit() else 443

    def _connect(self):
        """This method implements the functionality of establishing a secure connection using TLS Extension"""
        self._socket_client = socket()
        self._socket_client.connect((self._host, self._port))
        self._ssl_client = Connection(Context(TLSv1_METHOD), self._socket_client)
        self._ssl_client.set_connect_state()
        self._ssl_client.set_tlsext_host_name(self._host)
        self._ssl_client.do_handshake()

    def _close(self):
        """This method implements the functional termination created connection"""
        self._ssl_client.close()
        del self._socket_client

    @property
    @connection
    def serial_number(self):
        """Returns  certificates serial number"""
        return self._ssl_client.get_peer_certificate().get_serial_number()

    @property
    @connection
    def certificate(self):
        """Returns  certificate"""
        return OpenSSL.crypto.dump_certificate(FILETYPE_PEM, self._ssl_client.get_peer_certificate())


@step(r'([\w]+) resolves into (.+) new ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    server = getattr(world, serv_as)

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
    wait_until(check_new_ip, args=(domain.name, server.public_ip), timeout=timeout,
                           error_text="Domain resolve not new IP")


@step(r'([\w]+)(?: (not))? get domain ([\w\d]+) matches ([\w\d]+) index page$')
def check_index(step, proto, revert, domain_as, vhost_as):
    revert = False if not revert else True
    domain = getattr(world, domain_as)
    vhost = getattr(world, vhost_as)

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

    world.check_index_page(nodes, proto, revert, domain.name, vhost_as)


@step(r'([\w]+) get domain ([\w\d/_]+) matches \'(.+)\'$')
def check_matches_in_domain(step, proto, domain_as, matched_text):
    uri = ''
    if '/' in domain_as:
        domain_as, uri = domain_as.split('/')
    domain = getattr(world, domain_as)
    LOG.info('Match text %s in domain %s' % (matched_text, domain.name))

    if proto.isdigit():
        url = 'http://%s:%s/%s' % (domain.name, proto, uri)
    else:
        url = '%s://%s/%s' % (proto, domain.name, uri)
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
    server = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain.name,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, server.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, server.public_ip))


@step('domain ([\w\d]+)(?:,([\w\d]+))? contains valid Cert and CACert(?: into ([\w\d]+))?')
def assert_check_cert(step, domain_as1, domain_as2=None, serv_as=None):

    domain1 = getattr(world, domain_as1)
    domain2 = getattr(world, domain_as2) if domain_as2 else None
    server = getattr(world, serv_as) if serv_as else None

    #Get local certs
    local_cert1 = resources('keys/httpd.crt').get()

    if domain2 and server:
        #Get local certs
        local_cert2 = resources('keys/httpd2.crt').get()

        #Get remote certs
        LOG.info('Try get remote certificate for domain: {0}'.format(domain1.name))
        remote_cert1 = OpenSSLSNI(domain1.name, 443).certificate
        LOG.debug('Remote certificate is {0}: '.format(remote_cert1))

        LOG.info('Try get remote certificate for domain: {0}'.format(domain2.name))
        remote_cert2 = OpenSSLSNI(domain2.name, 443).certificate
        LOG.debug('Remote certificate is: {0}'.format(remote_cert2))

        LOG.info('Try get remote certificate by ip: {0}'.format(server.public_ip))
        remote_cert_by_ip = OpenSSLSNI(server.public_ip, 443).certificate
        LOG.debug('Remote certificate is: {0}'.format(remote_cert_by_ip))

        #Assert Certificates
        world.assert_equal(remote_cert1, remote_cert2, "Domains {0} and {1} are not unique certificates".format(domain1.name, domain2.name))
        LOG.info('Domains {0} and {1} are unique certificates'.format(domain1.name, domain2.name))

        world.assert_not_equal(remote_cert1, local_cert1, '{0} domain certificate does not match the local certificate'.format(domain1.name))
        LOG.info('{0} domain certificate matched the local certificate'.format(domain1.name))

        world.assert_not_equal(remote_cert2, local_cert2, '{0} domain certificate does not match the local certificate'.format(domain2.name))
        LOG.info('{0} domain certificate matched the local certificate'.format(domain2.name))

        world.assert_not_equal(remote_cert1, remote_cert_by_ip, 'Certificate obtained by the ip {0} does not match the certificate domain {1}'.format(server.public_ip, domain1.name))
        LOG.info('Certificate obtained by the ip {0} matched the certificate domain {1}'.format(server.public_ip, domain1.name))

    else:
        #Get remote certs
        cert = ssl.get_server_certificate((domain1.name, 443))
        #Assert Certificates
        world.assert_not_equal(cert, local_cert1, 'Cert not match local cert')


@step(r'my IP in ([\w]+) ([\w]+)([ \w]+)? access logs$')
def check_rpaf(step, serv_as, domain_as, ssl=None):
    LOG.debug('Check mod_rpaf')
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    domain = getattr(world, domain_as)
    path = '/var/log/http-%s-access.log' % domain.name
    LOG.info('Check my IP in %s log' % path)
    out = node.run('cat %s' % path)
    LOG.debug('Access log (%s) contains: %s' % (path, out[0]))
    ip = world.get_external_local_ip()
    if not ip in out[0]:
        raise AssertionError('Not see my IP in access log')
    LOG.info('My public IP %s in %s access log' % (ip, server.id))