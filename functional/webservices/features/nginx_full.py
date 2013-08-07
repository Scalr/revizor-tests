import re
import logging
import time
import requests

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.fixtures import resources


LOG = logging.getLogger('nginx-full')


@step(r'([\w]+) get (.+) matches (.+) index page$')
def check_index(step, proto, vhost_name, vhost2_name):
    domain = getattr(world, vhost_name)
    for vh in world.farm.vhosts: # Find vhost by domain
        if vh.name == domain:
            vhost = vh
            LOG.info('VHost for domain %s is %s' % (domain, vhost.id))
            break
    else:
        raise AssertionError('Can\'t find vhost for domain %s' % domain)

    for role in world.farm.roles: # Find role by vhost
        if role.id == vhost.farm_roleid:
            app_role = role
            break
    else:
        raise AssertionError('Can\'t find role for vhost %s' % vhost.id)

    nodes = []
    for s in app_role.servers: # delete pre-defined index.html file and upload vhost file
        if not s.status == 'Running':
            continue
        node = world.cloud.get_node(s)
        nodes.append(node)
        try:
            LOG.info('Delete index.html in server %s' % s.id)
            node.run('rm /var/www/%s/index.html' % vhost_name)
        except AttributeError, e:
            LOG.error('Failed in delete index.html: %s' % e)

    world.check_index_page(nodes, proto, domain, vhost2_name)
    world._domain = domain

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
    LOG.info('Add proxy to app role for domain %s' % vhost)
    backends = [{"farm_role_id": backend_role.id, "port": "80", "backup": "0", "down": "0", "location": "/"}]
    proxy_role.add_nginx_proxy(vhost, port, backends=backends, **opts)
    setattr(world, '%s_proxy' % proxy_name, {"hostname": vhost, "port": port, "backends": backends})


@step(r'([\w]+) proxies list should contains (.+)')
def check_proxy_in_config(step, www_serv, vhost_name):
    serv = getattr(world, www_serv)
    domain = getattr(world, vhost_name)
    node = world.cloud.get_node(serv)
    config = node.run('cat /etc/nginx/proxies.include')[0]
    LOG.info('Proxies config for server %s' % serv.public_ip)
    LOG.info(config)
    if not domain in config:
        raise AssertionError('Not see domain %s in proxies.include' % domain)


@step(r"I modify proxy ([\w\d]+) in ([\w\d]+) role (with|without) ip_hash and proxies: '(['\w\d \.]*)'")
def modify_proxy(step, proxy, role, ip_hash, options):
    LOG.info('Modify proxy %s with backends: %s' % (proxy, options))
    proxy = getattr(world, '%s_proxy' % proxy)
    role = getattr(world, '%s_role' % role)
    ip_hash = True if ip_hash == 'with' else False
    options = options.strip().replace('\'', '').split()
    options = zip(*[options[i::2] for i in range(2)])
    backends = []
    for o in options:
        serv = getattr(world, o[0], None)
        backends.append({
            "host": serv.public_ip if serv else o[0],
            "port": "80",
            "backup": "1" if o[1] == 'backup' else "0",
            "down": "1" if o[1] == 'down' else "0",
            "location": "/"
        })
    LOG.info("Save proxy changes with backends: %s" % backends)
    role.edit_nginx_proxy(proxy['hostname'], proxy['port'], backends, ip_hash=ip_hash)


@step(r"I delete proxy ([\w\d]+) in ([\w\d]+) role")
def delete_nginx_proxy(step, proxy, role):
    proxy = getattr(world, '%s_proxy' % proxy)
    role = getattr(world, '%s_role' % role)
    role.delete_nginx_proxy(proxy['hostname'])


@step(r"'([\w\d_ \.]+)' in ([\w\d]+) upstream file")
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
        serv = getattr(world, option[0], None)
        hostname = serv.public_ip if serv else option[0]
        if option[1] == 'default':
            c = "%s:80;" % hostname
        else:
            c = "%s:80 %s;" % (hostname, option[1])
        LOG.info('Verify \'%s\' in upstream' % c)
        if not c in options:
            return AssertionError('Upstream config not contains "%s"' % c)


@step(r"([\w\d]+) upstream list should be clean")
def validate_clean_upstream(step, serv_as):
    #TODO: Rewrite this when nginx will work via API
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    upstream = node.run('cat /etc/nginx/app-servers.include')[0]
    LOG.info('Upstream list: %s' % upstream)
    if upstream.strip():
        raise AssertionError('Upstream list not clean')
    # upstream = upstream.replace(re.findall(r"(upstream backend \{(?:.*)\})", upstream, re.MULTILINE | re.DOTALL)[0], '')
    # ips = re.findall(r"((?:\d+\.?){4};)", upstream)
    # if ips:
    #     raise AssertionError('Upstream list has IP adresses: %s' % ips)


@step(r"([\w\d]+) http( not)? redirect to ([\w\d]+) https")
def check_redirect(step, source_vhost, has_not, dest_vhost):
    LOG.debug("Check redirecting")
    LOG.debug("Source: %s; redirect: %s; dest host: %s" % (source_vhost, has_not, dest_vhost))
    if has_not.strip():
        has_not = True
    else:
        has_not = False
    source_vhost = getattr(world, source_vhost)
    dest_vhost = getattr(world, dest_vhost)
    r = requests.get(source_vhost)
    if has_not:
        if not r.history:
            return True
        raise AssertionError("http://%s redirect to %s" % (source_vhost, r.history[0].url))
    if r.history:
        if r.history[0].status_code == 301 and r.history[0].url == 'https://%s' % dest_vhost:
            return True
        raise AssertionError("http://%s not redirect to https://%s" % (source_vhost, dest_vhost))