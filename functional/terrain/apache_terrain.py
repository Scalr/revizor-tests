# coding: utf-8

"""
Created on 08.19.2014
@author: Eugeny Kurkovich
"""

import requests
from requests.exceptions import HTTPError, ConnectionError, SSLError
import logging
from lettuce import world, step

LOG = logging.getLogger(__name__)

@step(r'(https|http)(?: (not))? get (.+) contains default welcome message')
def assert_check_http_get_answer(step, proto, revert, serv_as):
    server = getattr(world, serv_as)
    verify = False if proto == 'https' else None
    revert = False if not revert else True
    try:
        resp = requests.get('%s://%s' % (proto, server.public_ip), timeout=15, verify=verify)
        msg = resp.text
    except (HTTPError, ConnectionError, SSLError), e:
        if not revert:
            LOG.error('Apache error: %s' % e.message)
            raise AssertionError('Apache error: %s' % e.message)
        else:
            msg = None

    LOG.debug('Step mode: %s. Apache message: %s' % ('not contains message' if revert else 'contains message', msg))
    apache_messages = ['It works!',
                       'Apache HTTP Server',
                       'Welcome to your Scalr application',
                       'Scalr farm configured succesfully',
                       'Amazon Linux AMI Test Page']
    if not revert and not any(message in msg for message in apache_messages):
        raise AssertionError('Not see default message, Received message: %s,  code: %s' % (msg, resp.status_code))
    elif revert and msg:
        raise AssertionError('Error. The message in default apache https mode. Received message: %s' % msg)


