import logging
import requests

from lettuce import world, step

from revizor2.api import Certificate, IMPL
from revizor2.conf import CONF
from revizor2.utils import wait_until

LOG = logging.getLogger(__name__)


def get_nginx_default_server_template():
    farm_settings = IMPL.farm.get_settings(world.farm.id)
    template = {
        "server": True,
        "content": farm_settings['tabParams']['nginx']['server_section'] +
                   farm_settings['tabParams']['nginx']['server_section_ssl']
    }
    return template


def check_config_for_option(node, config_file, option):
    config = node.run('cat /etc/nginx/%s' % config_file)[0]
    if config_file == 'proxies.include':
        config = ' '.join(config.split())
    if option in config:
        return config


@step(r'([\w]+) proxies list should contains (.+)')
def check_proxy_in_nginx_config(step, www_serv, vhost_name):
    serv = getattr(world, www_serv)
    domain = getattr(world, vhost_name)
    node = world.cloud.get_node(serv)
    LOG.info('Proxies config for server %s' % serv.public_ip)
    wait_until(check_config_for_option,
               args=[node, 'proxies.include', domain.name],
               timeout=180,
               error_text='Not see domain %s in proxies.include' % domain)


@step(r"I modify proxy ([\w\d]+) in ([\w\d]+) role (with|without) ip_hash and proxies:")
def modify_nginx_proxy(step, proxy, role_type, ip_hash):
    """
    Modify nginx proxy settings via farm builder, use lettuce multiline for get proxy settings.
    If string in multiline startswith '/', this line will parsing as backend:
    first - location
    second - server with port
    third - settings (default, backup, disabled)
    after third and to end of line - template for location
    """
    LOG.info('Modify proxy %s with backends:\n %s' % (proxy, step.multiline))
    proxy = getattr(world, '%s_proxy' % proxy)
    role = world.get_role(role_type)
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
            'backup': '0',
            'weight': '',
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

        template = ''
        if len(splitted_line) > 3:
            if splitted_line[3].isdigit():
                backend['weight'] = splitted_line[3]
                template = " ".join(splitted_line[4:])
            else:
                template = " ".join(splitted_line[3:])

        if not backend['location'] in templates:
            templates[backend['location']] = [template]
        else:
            templates[backend['location']].append(template)
        backends.append(backend)
    default_server_template = get_nginx_default_server_template()
    new_templates = []
    for location in templates:
        if location == 'server':
            new_templates.append({
                'content': '\n'.join(templates[location]) + default_server_template['content'],
                'server': True
            })
        else:
            new_templates.append({
                'location': location,
                'content': '\n'.join(templates[location]),
            })

    LOG.info("Save proxy changes with backends:\n%s\n templates:\n%s" % (backends, new_templates))
    role.edit_nginx_proxy(proxy['hostname'], proxy['port'], backends, new_templates, ip_hash=ip_hash)


@step(r"I delete proxy ([\w\d]+) in ([\w\d]+) role")
def delete_nginx_proxy(step, proxy_name, proxy_role):
    proxy = getattr(world, '%s_proxy' % proxy_name)
    role = world.get_role(proxy_role)
    role.delete_nginx_proxy(proxy['hostname'])


@step(r"'([\w\d_ =:\.]+)' in ([\w\d]+) upstream file")
def check_options_in_nginx_upstream(step, option, serv_as):
    option = option.split()
    host, backend_port = option[0].split(':') if ':' in option[0] else (option[0], 80)
    server = getattr(world, serv_as)

    if CONF.feature.dist.is_centos and CONF.feature.dist.version >= 7:
        wait_until(world.check_open_port,
                   args=(server, backend_port),
                   timeout=60,
                   error_text="Port %s on host %s is not open" % (backend_port, host))

    node = world.cloud.get_node(server)
    LOG.info('Verify %s in upstream config' % option)
    if len(option) == 1:
        wait_until(check_config_for_option,
                   args=[node, 'app-servers.include', option[0]],
                   timeout=180,
                   error_text="Options '%s' not in upstream config: %s" % (
                       option, node.run('cat /etc/nginx/app-servers.include')[0]))
    elif len(option) > 1:
        serv = getattr(world, host, None)
        hostname = serv.private_ip if serv else host
        if option[1] == 'default':
            upstream_url = "%s:%s;" % (hostname, backend_port)
        else:
            upstream_url = "%s:%s %s;" % (hostname, backend_port, option[1])
        if option[-1].startswith('weight'):
            upstream_url = upstream_url.replace(';', ' %s;' % option[-1])
        LOG.info('Verify \'%s\' in upstream' % upstream_url)
        wait_until(check_config_for_option,
                   args=[node, 'app-servers.include', upstream_url],
                   timeout=180,
                   error_text='Upstream config not contains "%s"' % upstream_url)


@step(r"'([\w\d_ :;\.]+)' in ([\w\d]+) proxies file$")
def check_options_in_nginx_upstream(step, option, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Verify %s in proxies config' % option)
    wait_until(check_config_for_option,
               args=[node, 'proxies.include', option],
               timeout=180, error_text='Parameter \'%s\' not found in proxies.include' % option)


@step(r"([\w\d]+) upstream list should be clean")
def validate_clean_nginx_upstream(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info("Check upstream in nginx server")
    upstream = node.run('cat /etc/nginx/app-servers.include')[0]
    LOG.info('Upstream list: %s' % upstream)
    if upstream.strip():
        raise AssertionError('Upstream list not clean')


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
