import ssl

from lettuce import world, step, after

import requests

from revizor2.utils import wait_until
from revizor2.fixtures import resources

import logging

#Uses for supporting TLS SNI
from socket import socket
import OpenSSL
from OpenSSL.SSL import TLSv1_METHOD, Context, Connection
from OpenSSL.crypto import FILETYPE_PEM


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
    serv = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain.name,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, serv.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, serv.public_ip))


@step('domain ([\w\d]+) contains valid Cert and CACert')
def assert_check_cert(step, domain_as):
    domain = getattr(world, domain_as)
    cert = ssl.get_server_certificate((domain.name, 443))
    local_cert = resources('keys/httpd.crt').get()
    world.assert_not_equal(cert, local_cert, 'Cert not match local cert')