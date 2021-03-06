import requests
from requests.exceptions import HTTPError, ConnectionError, SSLError
import logging

from revizor2.api import Server


LOG = logging.getLogger(__name__)

APACHE_MESSAGES = (
    'It works!',
    'Apache HTTP Server',
    'Welcome to your Scalr application',
    'Scalr farm configured succesfully',
    'Amazon Linux AMI Test Page',
    'Ok'
)


def assert_check_http_get_answer(server: Server, proto: str='http', revert: bool=False):
    verify = False if proto == 'https' else None
    revert = False if not revert else True
    try:
        resp = requests.get(
            '%s://%s' % (proto, server.public_ip), timeout=15, verify=verify)
        msg = resp.text
    except (HTTPError, ConnectionError, SSLError) as e:
        if not revert:
            LOG.error('Apache error: %s' % e)
            raise AssertionError('Apache error: %s' % e)
        else:
            msg = None

    LOG.debug('Step mode: %s. Apache message: %s' %
              ('not contains message' if revert else 'contains message', msg))
    if not revert and not any(message in msg for message in APACHE_MESSAGES):
        raise AssertionError(
            'Not see default message, Received message: %s,  code: %s' % (msg, resp.status_code))
    elif revert and msg:
        raise AssertionError(
            'Error. The message in default apache https mode. Received message: %s' % msg)
