__author__ = 'gigimon'

import re
import logging
import time
import requests

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.fixtures import resources


LOG = logging.getLogger('haproxy-full')


@step("I add proxy ([\w\d]+) to ([\w\d]+) role for ([\d]+) port with ([\w\d]+) role backend")
def add_proxy_to_role(step, proxy_name, proxy_role, port, backend_role):
    LOG.info("Add haproxy proxy %s with role backend" % proxy_name)
    proxy_role = getattr(world, '%s_role' % proxy_role)
    backend_role = getattr(world, '%s_role' % backend_role)
    backends = [{
        'farm_role_id': backend_role.id,
        'port': str(port),
        'backup': '0',
        'down': '0'
    }]
    proxy_role.add_haproxy_proxy(port, backends)



def parse_haproxy_config(node):
    config = node.run('cat /etc/haproxy/haproxy.cfg')[0].splitlines()
    listens = {}
    backends = {}

    return listens, backends