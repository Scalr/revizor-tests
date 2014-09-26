# coding: utf-8

"""
Created on 08.18.2014
@author: Eugeny Kurkovich
"""

import logging
import requests
from time import time
from lettuce import world, step
from revizor2.utils import wait_until
from revizor2 import szrapi
from revizor2.defaults import DEFAULT_API_TEMPLATES as templates
from revizor2.api import Certificate



LOG = logging.getLogger(__name__)


def run_api(serv_as, command, api_args):
    server = getattr(world, serv_as)
    api = getattr(getattr(szrapi, 'ApacheApi')(server), command)
    # Set vhost args
    setattr(world, ''.join((command, '_args')), api_args)
    api_result = api(**api_args)
    setattr(world, ''.join((command, '_res')), api_result)
    return api_result


@step(r'api result (\"\w+\") does not contain argument (\"\w+\") from command ("delete_vhosts")')
def assert_vhost_delete(step, res_storage_name, input_arg_name, args_storage_name):
    """
        :param res_storage_name: attribute name in world stored api result
        :param input_arg_name: attribute name in world stored api input arguments
        :param args_storage_name:
    """

    # Get api command input args storage
    storage_name = ''.join((args_storage_name.replace('"', ''), '_args'))

    # Get api command input argument
    input_arg = getattr(world, storage_name)[input_arg_name.strip().replace('"', '')]
    LOG.debug('Obtained api command {0} input argument {1}: {2}'.format(
        args_storage_name,
        input_arg_name,
        input_arg))

    # Get api command result
    api_result = getattr(world, ''.join((res_storage_name.strip().replace('"', ''), '_res')))
    LOG.debug('Obtained api command {0} result: {1}'.format(
        res_storage_name,
        api_result))

    # Check api command result
    if not isinstance(api_result, (list, tuple)):
        raise Exception('Mismatch api command result: {0} output format: {1}'.format(
            res_storage_name,
            type(api_result)
        ))
    assertion_list = [filter(lambda vhost: arg[0] in vhost, api_result) for arg in input_arg]
    assertion_message = 'Obtained list virtual hosts {0} contains some records: {1} from {2} arguments: {3}'.format(
        api_result,
        assertion_list,
        args_storage_name,
        input_arg)
    assert all(not len(vhost) for vhost in assertion_list), assertion_message
    LOG.debug('Obtained list virtual hosts {0} not contains any records from {1} arguments: {2}'.format(
        api_result,
        args_storage_name,
        input_arg))


@step(r'I create domain ([\w\d]+)')
def create_domain(step, domain_as):
    LOG.info('Create domain as {0}'.format(domain_as))
    role = world.get_role()
    domain = role.create_domain()
    LOG.info('New domain was successfully created as :{0}'.format(domain.name))
    setattr(world, domain_as, domain)


@step(r'I add ssl virtual host with key ([\w\d-]+) to domain ([\w\d]+) on ([\w\d]+)')
def create_vhost(step, key_name, domain_as, serv_as):
    domain = getattr(world, domain_as)
    # Set vhost args
    args = dict(
        hostname=domain.name,
        port=443,
        template=templates['ApacheApi']['ssl-name-based-template'].replace('www.secure.example.com', domain.name),
        ssl=True,
        ssl_certificate_id=Certificate.get_by_name(key_name).id,
        reload=True)
    res = run_api(serv_as, 'create_vhost', args)
    LOG.info('Add new virtual hosts to domain {0} with key {1}:\n{2}'.format(
        domain.name,
        key_name,
        res))


@step(r'I update virtual host on domain ([\w\d]+) from ssl to plain-text on ([\w\d]+)')
def update_hhost(step, domain_as, serv_as):
    domain = getattr(world, domain_as)
    # Set vhost args
    args = dict(
        signature=(domain.name, 443),
        hostname=domain.name,
        port=80,
        template=templates['ApacheApi']['name-based-template'].replace('www.example.com', domain.name),
        ssl=False,
        reload=True)
    res = run_api(serv_as, 'update_vhost', args)
    LOG.info('Virtual hosts on domain {0} was updated:\n{1}'.format(domain.name, res))


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, domain_as, serv_as, timeout=1800):
    domain = getattr(world, domain_as)
    server = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving,
                           args=(domain.name,),
                           timeout=timeout,
                           error_text='Domain: {0} not resolve'.format(domain.name))
    assert domain_ip == server.public_ip, 'Domain IP {0} != server IP {1}'.format(
        domain_ip,
        server.public_ip)


@step(r'domain ([\w\d]+) contain default web page')
def assert_default_page(step, domain_as,):
    domain = getattr(world, domain_as)
    url = 'http://%s/' % domain.name
    for i in xrange(10):
        LOG.info('Try get index from URL: %s, attempt %s ' % (url, i+1))
        try:
            resp = requests.get(url, timeout=30, verify=False)
            break
        except Exception, e:
            LOG.warning("Error in openning page '%s': %s" % (url, e))
            time.sleep(15)
    else:
        raise AssertionError("Can't domain {0} default page: {1}".format(domain.name, url))
    assertion_text = 'If you can see this page, it means that your Scalr farm configured succesfully.'
    assertion_message = 'Default page not valid: {0}.\nStatus code: {1}'.format(resp.text, resp.status_code)
    assert resp.text == assertion_text and resp.status_code == 200, assertion_message