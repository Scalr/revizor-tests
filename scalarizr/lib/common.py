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


