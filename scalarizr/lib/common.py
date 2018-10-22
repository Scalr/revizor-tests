import logging
import re

import requests
import semver

from revizor2 import CONF

LOG = logging.getLogger(__name__)


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
