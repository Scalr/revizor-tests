import ssl
import time
import logging
import requests

from requests import exceptions
from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Platform, Dist
from revizor2.utils import wait_until
from revizor2.fixtures import resources
from revizor2.defaults import DEFAULT_SSL_CERTS

LOG = logging.getLogger(__name__)


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
    #TODO: Rewrite this ugly
    revert = False if not revert else True
    domain = getattr(world, domain_as)
    vhost = getattr(world, vhost_as)
    domain_address = domain.name

    if CONF.feature.driver.cloud_family == Platform.CLOUDSTACK:
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
    for i in range(3):
        LOG.info('Try open url: "%s" attempt: %s' % (url, i))
        try:
            resp = requests.get(url).text
            if resp == matched_text:
                break
        except:
            pass
        time.sleep(5)
    else:
        raise AssertionError('Text "%s" not matched with "%s"' % (resp, matched_text))


@step('I start BaseHttpServer on (\d+) port in ([\w\d]+)$')
def start_basehttpserver(step, port, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Run BaseHttpServer in server %s' % server.id)
    node = world.cloud.get_node(server)
    LOG.debug('Put base_server.py script')
    node.put_file('/tmp/base_server.py', resources('scripts/base_server.py').get())
    LOG.debug('Run BaseHttpServer script')
    if Dist.is_debian_family(CONF.feature.dist):
        node.run('apt-get install screen -y')
    elif Dist.is_centos_family(CONF.feature.dist):
        node.run('yum install screen -y')
    node.run('iptables -I INPUT 1 -p tcp --dport %s -j ACCEPT' % port)
    if node.run('which python3')[2] == 0:
        python_alias = 'python3'
    else:
        python_alias = 'python'
    node.run('screen -d -m %s /tmp/base_server.py %s' % (python_alias, port))


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    server = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain.name,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, server.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, server.public_ip))


@world.run_only_if(dist=['!centos5'])
@step(r'virtual host has a valid SSL certificate')
def check_virtual_host_certificate(step):
    for host_hash in step.hashes:
        obj = getattr(world, host_hash['source_name'])
        cert_key = DEFAULT_SSL_CERTS.get(host_hash['key'])
        # hostname  handler
        if host_hash['source'] == 'domain':
            key = cert_key.get('key_name')
            url = 'https://%s' % obj.name
            for _ in xrange(10):
                try:
                    res = requests.get(url, verify=key)
                    LOG.debug('Remote host %s request result: %s' % (url, res.text))
                    break
                except exceptions.SSLError as e:
                    raise RuntimeError('Can not verify remote cert with local key: %s\n%s' % (key, e.message))
                except Exception as e:
                    LOG.error('%s' % e.message)
                    time.sleep(3)
            else:
                raise AssertionError('Can not retrieve content from remote host: %s.' % url)
        # ip handler
        elif host_hash['source'] == 'server':
            server_cert = ssl.get_server_certificate((obj.public_ip, 443))
            LOG.debug('Server %s SSL certifacate: %s' % (obj.public_ip, server_cert))
            assert server_cert == cert_key.get('cert'), 'Sever %s certificate do not match local' % obj.public_ip


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