# coding: utf-8
"""
Created on 08.24.2015
@author: Eugeny Kurkovich
"""
import os
import hmac
import json
import time
import gevent
import hashlib
import logging
import binascii
import requests

from revizor2 import CONF
from urllib import urlencode
from revizor2.api import IMPL
from lettuce import world, step
from collections import namedtuple
from urlparse import urlparse, urlunparse

LOG = logging.getLogger(__name__)

CONST = namedtuple(
    'CONST',
        'api_path, '
        'api_date_fmt, '
        'api_host, '
        'api_scheme, '
        'api_debug')(
            '/api/user/v1beta0/{envid}/{api_method}/',
            '%Y-%m-%dT%H:%M:%SZ',
            urlparse(CONF.backends.scalr.cpanel_url).hostname,
            os.environ.get('API_SCHEME') or 'http',
            1
    )

def send_request(key, uri, params=None, body=None):
    secretKey = key.get('secretKey')
    keyId = key.get('keyId')
    jsonEncodedBody = json.dumps(body) if body else ''

    # date_format
    # /2015-02-17T13:54:06Z
    sig_date = time.strftime(CONST.api_date_fmt, time.gmtime())
    LOG.debug('Sign date: %s' % sig_date)

    # Set string to sign
    canonicalQueryString = ''
    if (params):
        canonicalQueryString = urlencode(
            sorted(params.items(), key=lambda x: x[0])
        )
    stringToSign = '\n'.join(('GET', sig_date, uri, canonicalQueryString, jsonEncodedBody))
    LOG.debug('String to sign: %s' % ''.join(stringToSign.split()))

    # Sign request
    digest = hmac.new(str(secretKey), str(stringToSign), hashlib.sha256).digest()
    sig = binascii.b2a_base64(digest)
    if sig.endswith('\n'):
        sig = sig[:-1]
    LOG.debug('X-Scalr-Signature : %s' % sig)

    # Set headers
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Scalr-Key-Id': str(keyId),
        'X-Scalr-Date': sig_date,
        'X-Scalr-Signature': ' '.join(('V1-HMAC-SHA256', sig)),
        'X-Scalr-Debug': CONST.api_debug
    }

    # Set endpoint
    endpoint_args = (
        CONST.api_scheme,
        CONST.api_host,
        uri,
        '', '', ''
    )
    endpoint = urlunparse(data=endpoint_args)
    LOG.debug('Endpoint : %s Header : %s' % (endpoint, headers))

    try:
        resp = requests.get(endpoint, params=params, headers=headers)
        resp.raise_for_status()
    except requests.HTTPError as e:
        LOG.error('An error occurred: Url: {url} Message: {message} Code: {code}'.format(
            url = resp.url,
            **resp.json().get('errors', [{'message': '', 'code': ''}])[0])
        )
    return resp

@step(r'I have ([\d]+) new api secret key(?:s)?')
def generate_new_keys(step, count):
    api_keys = getattr(IMPL, 'api_key')

    LOG.info('Generate %s new scalr api v.2 keys' % count)
    keys_count = len(api_keys.list())
    keys = [api_keys.new() for _ in xrange(int(count))]
    assert len(api_keys.list())-keys_count == int(count), 'Api keys was not properly generated'

    setattr(world, 'keys', keys)
    LOG.debug('Generated keys: %s' % keys)

@step(r'I generate (more\sthan\s)?([\d]+) api queries for one minute(\susing second secret key)?')
def send_api_requests(step, inc_count, queries_count, key_id):

    def task():
        resp = send_request(key, uri, dict(maxResults=2))
        return resp.status_code

    key = getattr(world, 'keys')[bool(key_id)]
    scalr_env = getattr(IMPL, 'account').get_env()
    uri = CONST.api_path.format(envid=scalr_env['env_id'], api_method='roles')

    queries_count = int(queries_count)+1 if inc_count else int(queries_count)
    tasks_end_time = time.time()+60

    tasks = [gevent.spawn(task) for _ in xrange(queries_count) if time.time() < tasks_end_time]
    gevent_result = gevent.joinall(tasks)
    tasks_result = [tr.value for tr in gevent_result]

    world.queries_count = queries_count
    world.tasks_results = tasks_result
    LOG.debug('Saved tasks results: %s' % tasks_result)

@step(r'limit error was (not\s)?triggered by scalr')
def check_api_result(step, no_errors):
    if no_errors:
        assert all(code == 200 for code in world.tasks_results), 'Limit error was triggered by Scalr'
        return

    for code in world.tasks_results:
        if code != 200:
            index = world.tasks_results.index(code)
            assert index == world.queries_count-1, \
                'Limit error was triggered by Scalr on task %s instead %s' % (index, world.count)
            break
    else:
        raise AssertionError('Limit error was not triggered by Scalr')

@step(r'I generate api queries with failed method')
def send_failed_request(step):
    key = getattr(world, 'keys')[0]
    scalr_env = getattr(IMPL, 'account').get_env()
    uri = CONST.api_path.format(envid=scalr_env['env_id'], api_method='failed')

    resp = send_request(key, uri, dict(maxResults=2))
    world.tasks_results = resp.status_code
    LOG.debug('Failed result: %s' % resp.json())

@step(r'The ([\d]+) error was triggered by scalr')
def chesk_error_code(step, error_code):
    assert int(error_code) == int(world.tasks_results), 'Error triggered  by scalr not valid'