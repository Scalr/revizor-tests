import logging
import re

import requests
import semver

from revizor2 import CONF
from revizor2.consts import Platform
from revizor2.backend import IMPL

LOG = logging.getLogger(__name__)

IP_RESOLVER_SITES = (
    'http://revizor2.scalr-labs.com/get_ext_ip/',
    'http://ifconfig.me/ip',
    'http://myexternalip.com/raw',
    'http://ip-address.ru/show'
)


def run_only_if(*args, **kwargs):
    """
    Accept parameters: platform, storage, dist, szr_version
    """
    if kwargs.get('szr_version'):
        repo_url = 'http://stridercd.scalr-labs.com/scalarizr/apt-plain/develop/%s/'
        if CONF.feature.branch in ['latest', 'stable']:
            repo_url = 'http://stridercd.scalr-labs.com/scalarizr/apt-plain/release/%s/'
        web_content = requests.get(repo_url % CONF.feature.branch).text
        m = re.search('scalarizr_(.+?).(\w+)-1_', web_content)
        if m:
            version = m.group(1).replace('b', '')
    current = []
    if kwargs.get('platform'):
        current.append(CONF.feature.platform.name)
    if kwargs.get('storage'):
        current.append(CONF.feature.storage)
    if kwargs.get('dist'):
        current.append(CONF.feature.dist.id)
    if kwargs.get('family'):
        current.append(CONF.feature.dist.family)
    options = []
    pass_list = []
    skip_list = []
    for v in kwargs.values():
        if isinstance(v, (dict, list, tuple)):
            for i in v:
                options.append(i)
        else:
            options.append(v)
    for v in options:
        if v.startswith('!'):
            skip_list.append(v.strip('!'))
        else:
            pass_list.append(v)

    def wrapper(func):
        def skipped(*a, **kw):
            LOG.debug('Step does not meet conditions, excluding: %s' % func.__name__)

        for c in current:
            if (not skip_list and c not in pass_list) or (skip_list and c in skip_list):
                return skipped
        if kwargs.get('szr_version') and not semver.match(version, kwargs.get('szr_version')):
            return skipped
        return func

    return wrapper


def get_external_local_ip():
    for site in IP_RESOLVER_SITES:
        try:
            LOG.debug('Try get external IP address from site %s' % site)
            my_ip = requests.get(site).text.strip()
            if not re.match('\d+\.\d+\.\d+\.\d+', my_ip):
                LOG.warning('Site %s not return my ip' % site)
                continue
            break
        except requests.ConnectionError:
            LOG.warning("Can't get external IP from site: %s, try next" % site)
    else:
        raise requests.ConnectionError("Can't get external IP from all sites in list")
    LOG.info('Current external IP address is %s' % my_ip)
    return my_ip


def get_platform_backend_tools():
    """
    Find platform backed by current platform name
    :return: backend object (IMPL.platform_name_tools)
    """
    platform_backend_tools = {
        Platform.AZURE: 'azure_tools',
        Platform.EC2: 'aws_tools',
        Platform.GCE: 'gce_tools'}
    return getattr(IMPL, platform_backend_tools.get(CONF.feature.platform.name))
