import re
import logging
import time
import requests

from lettuce import world, step

from revizor2.api import Certificate
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
        opts['cert_id'] = Certificate.get_by_name('revizor').id
        opts['http'] = True
    elif proto == 'http/https':
        LOG.info('Add http/https proxy')
        port = 80
        opts['ssl'] = True
        opts['ssl_port'] = 443
        opts['cert_id'] = Certificate.get_by_name('revizor').id
    if ip_hash:
        opts['ip_hash'] = True
    LOG.info('Add proxy to app role for domain %s' % vhost.name)
    backends = [{"farm_role_id": backend_role.id, "port": "80", "backup": "0", "down": "0", "location": "/"}]
    proxy_role.add_nginx_proxy(vhost.name, port, templates=[], backends=backends, **opts)
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


@step(r"I modify proxy ([\w\d]+) in ([\w\d]+) role (with|without) ip_hash and proxies:")
def modify_proxy(step, proxy, role, ip_hash):
    """
    Modify nginx proxy settings via farm builder, use lettuce multiline for get proxy settings.
    If string in multiline startswith '/', this line will parsing as backend:
    first - location
    second - server with port
    third - settings (default, backup, disabled)
    after third and to end of line - template for location
    """
    LOG.info('Modify proxy %s with backends:\n %s' % (proxy, step.multiline))
    #proxy = getattr(world, '%s_proxy' % proxy)
    #role = getattr(world, '%s_role' % role)
    ip_hash = True if ip_hash == 'with' else False
    backends = []
    templates = {'server': []}
    for line in step.multiline.splitlines():
        line = line.strip()
        if not line.startswith('/'):
            templates['server'].append(line.strip())
            continue
        backend = {
            'down': '0',
            'backup': '0'
        }
        splitted_line = line.split()
        LOG.info('Splitted line: %s' % splitted_line)
        backend['location'] = splitted_line[0]

        if ':' in splitted_line[1]:
            host, backend['port'] = splitted_line[1].split(':')
        else:
            host = splitted_line[1]
            backend['port'] = 80
        host = getattr(world, host, host)
        if not isinstance(host, (str, unicode)):
            host = host.private_ip
        backend['host'] = host
        # Check disabled/backup otions
        if not splitted_line[2] == 'default':
            backend[splitted_line[2]] = '1'

        template = " ".join(splitted_line[3:])
        if not backend['location'] in templates:
            templates[backend['location']] = [template]
        else:
            templates[backend['location']].append(template)
        backends.append(backend)
    new_templates = []
    for location in templates:
        if location == 'server':
            new_templates.append({
                'content': '\n'.join(templates[location]),
                'server': True
            })
        else:
            new_templates.append({
                'location': location,
                'content': '\n'.join(templates[location]),
            })
    LOG.info("Save proxy changes with backends:\n%s\n templates:\n%s" % (backends, new_templates))
    role.edit_nginx_proxy(proxy['hostname'], proxy['port'], backends, new_templates, ip_hash=ip_hash)


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
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info("Check upstream in nginx server")
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