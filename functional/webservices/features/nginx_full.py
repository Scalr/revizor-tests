import re
import logging
import time
import requests

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.fixtures import resources


LOG = logging.getLogger('nginx-full')


@step(r"I add (http|https|http/https) proxy (\w+) to (\w+) role with ([\w\d]+) host to (\w+) role( with ip_hash)?")
def add_proxy_with_role(step, proto, proxy_name, proxy_role, vhost_name, backend_role, ip_hash):
    """
    If http/https then http -> https redirect enable
    If https - redirect disable
    """
    proxy_role = getattr(world, '%s_role' % proxy_role)
    backend_role = getattr(world, '%s_role' % backend_role)
    vhost = getattr(world, vhost_name)
    opts = {}
    if proto == 'http':
        LOG.info('Add http proxy')
        port = 80
    elif proto == 'https':
        LOG.info('Add https proxy')
        port = 80
        opts['ssl'] = True
        opts['ssl_port'] = 443
        opts['cert_id'] = 801
        opts['http'] = True
    elif proto == 'http/https':
        LOG.info('Add http/https proxy')
        port = 80
        opts['ssl'] = True
        opts['ssl_port'] = 443
        opts['cert_id'] = 801
    if ip_hash:
        opts['ip_hash'] = True
    LOG.info('Add proxy to app role for domain %s' % vhost.name)
    backends = [{"farm_role_id": backend_role.id, "port": "80", "backup": "0", "down": "0", "location": "/"}]
    proxy_role.add_nginx_proxy(vhost.name, port, backends=backends, **opts)
    setattr(world, '%s_proxy' % proxy_name, {"hostname": vhost.name, "port": port, "backends": backends})


@step(r'([\w]+) proxies list should contains (.+)')
def check_proxy_in_config(step, www_serv, vhost_name):
    serv = getattr(world, www_serv)
    domain = getattr(world, vhost_name)
    node = world.cloud.get_node(serv)
    config = node.run('cat /etc/nginx/proxies.include')[0]
    LOG.info('Proxies config for server %s' % serv.public_ip)
    LOG.info(config)
    if not domain.name in config:
        raise AssertionError('Not see domain %s in proxies.include' % domain)


@step(r"I modify proxy ([\w\d]+) in ([\w\d]+) role (with|without) ip_hash and proxies: '(['\w\d :\.]*)'")
def modify_proxy(step, proxy, role, ip_hash, options):
    LOG.info('Modify proxy %s with backends: %s' % (proxy, options))
    proxy = getattr(world, '%s_proxy' % proxy)
    role = getattr(world, '%s_role' % role)
    ip_hash = True if ip_hash == 'with' else False
    options = options.strip().replace('\'', '').split()
    options = zip(*[options[i::2] for i in range(2)])
    backends = []
    for o in options:
        if ':' in o[0]:
            host, backend_port = o[0].split(':')
        else:
            host = o[0]
            backend_port = 80
        serv = getattr(world, host, None)
        backends.append({
            "host": serv.public_ip if serv else host,
            "port": str(backend_port),
            "backup": "1" if o[1] == 'backup' else "0",
            "down": "1" if o[1] == 'down' else "0",
            "location": "/"
        })
    LOG.info("Save proxy changes with backends: %s" % backends)
    role.edit_nginx_proxy(proxy['hostname'], proxy['port'], backends, ip_hash=ip_hash)


@step(r"I delete proxy ([\w\d]+) in www role")
def delete_nginx_proxy(step, proxy):
    proxy = getattr(world, '%s_proxy' % proxy)
    role = getattr(world, 'www_role')
    role.delete_nginx_proxy(proxy['hostname'])


@step(r"'([\w\d_ :\.]+)' in ([\w\d]+) upstream file")
def check_options_in_upstream(step, option, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    options = node.run('cat /etc/nginx/app-servers.include')[0]
    LOG.info('Verify %s in upstream config' % option)
    option = option.split()
    if len(option) == 1:
        if option[0] in options:
            return True
        else:
            raise AssertionError("Options '%s' not in upstream config: %s" % (option, options))
    elif len(option) == 2:
        if ':' in option[0]:
            host, backend_port = option[0].split(':')
        else:
            host = option[0]
            backend_port = 80
        serv = getattr(world, host, None)
        hostname = serv.public_ip if serv else host
        if option[1] == 'default':
            c = "%s:%s;" % (hostname, backend_port)
        else:
            c = "%s:%s %s;" % (hostname, backend_port, option[1])
        LOG.info('Verify \'%s\' in upstream' % c)
        if not c in options:
            return AssertionError('Upstream config not contains "%s"' % c)


@step(r"([\w\d]+) upstream list should be clean")
def validate_clean_upstream(step, serv_as):
    #TODO: Rewrite this when nginx will work via API
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info("Check upstream in ngin server")
    upstream = node.run('cat /etc/nginx/app-servers.include')[0]
    LOG.info('Upstream list: %s' % upstream)
    if upstream.strip():
        raise AssertionError('Upstream list not clean')
    # upstream = upstream.replace(re.findall(r"(upstream backend \{(?:.*)\})", upstream, re.MULTILINE | re.DOTALL)[0], '')
    # ips = re.findall(r"((?:\d+\.?){4};)", upstream)
    # if ips:
    #     raise AssertionError('Upstream list has IP adresses: %s' % ips)


@step(r"([\w\d]+) http( not)? redirect to ([\w\d]+) https")
def check_redirect(step, src_domain_as, has_not, dst_domain_as):
    LOG.debug("Check redirecting")
    source_domain = getattr(world, src_domain_as)
    dst_domain = getattr(world, dst_domain_as)
    LOG.debug("Source: %s; redirect: %s; dest host: %s" % (source_domain.name, has_not, dst_domain.name))
    if has_not:
        has_not = True
    else:
        has_not = False
    r = requests.get('http://%s' % source_domain.name, verify=False)
    if has_not:
        if not r.history:
            return True
        raise AssertionError("http://%s redirect to %s" % (source_domain.name, r.history[0].url))
    if r.history:
        if r.history[0].status_code == 301 and r.url.startswith('https://%s' % dst_domain.name):
            return True
        raise AssertionError("http://%s not redirect to https://%s" % (source_domain.name, dst_domain.name))