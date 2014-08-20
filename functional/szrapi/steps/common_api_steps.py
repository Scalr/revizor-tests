# coding: utf-8

"""
Created on 08.18.2014
@author: Eugeny Kurkovich
"""

import logging

from lettuce import world, step

from revizor2 import szrapi
from revizor2.defaults import DEFAULT_API_TEMPLATES as templates

LOG = logging.getLogger(__name__)


@step(r'I run (.+) command (.+) on (\w+)(?: (.+))?')
def run_api_command(step, service_api, command, serv_as, isset_args=None):
    """
        :param service_api: Service Api class name
        :param command: Api command
        :param serv_as: Server name
        :param isset_args: Is api command has extended arguments
    """
    # Set attributes
    server = getattr(world, serv_as)
    service_api = service_api.strip().replace('"', '')
    command = command.strip().replace('"', '')

    # Get service api
    api = getattr(getattr(szrapi, service_api)(server), command)
    LOG.debug('Obtained %s instance %s for server %s' % (service_api, api, server.id))
    # Get api arguments
    args = None
    if isset_args:
        args = dict([key, templates[service_api][value.lower()] if value.isupper() else value] \
            for key,value in step.hashes[0].iteritems())
        setattr(world, 'api_args', args)
        LOG.debug('Obtained {0}.{1} extended arguments: {2}'.format(
            service_api,
            command,
            args
        ))
    # Run api command
    try:
        api_result = api(**args) if args else api()
        LOG.debug('Run %s instance method %s.' % (service_api, command))
        if api_result:
            setattr(world, command, api_result)
            LOG.debug('Obtained {0} instance method {1} result: {2}'.format(
                service_api,
                command,
                api_result))
    except Exception as e:
        raise Exception('An error occurred while try to run: {0}.\nScalarizr api Error: {1}'.format(
            command,
            e.message)
        )


@step(r'And api result (.+) has(?: (.+))? argument (.+)')
def assert_api_result(step, res_storage_name, negation, input_arg_name):

    """
        :param res_storage_name: attribute name in world stored api result
        :param negation: negation
        :param input_arg_name: attribute name in world stored api input arguments
    """
    try:
        # Get api command result
        result = getattr(world, res_storage_name.strip().replace('"', ''))
        LOG.debug('Obtained api command {0} result: {1}'.format(
            res_storage_name,
            result))

        # Get api input argument
        input_arg = getattr(world, 'api_args')[input_arg_name.strip().replace('"', '')]
        LOG.debug('Obtained api command {0} input argument {1}: {2}'.format(
            res_storage_name,
            input_arg_name,
            input_arg))

        # Check api result
        if isinstance(result, (list, tuple)):
            assert all(input_arg not in res for res in result) if negation \
                else any(input_arg in res for res in result)
        elif isinstance(result, str):
            assert (input_arg not in result) if negation \
                else (input_arg in result)
        LOG.debug('Result of the command: {0}:{1} {2}contains '
                  'the value of the input argument: {3}:{4}'.format(
            res_storage_name,
            result,
            'not ' if negation else '',
            input_arg_name,
            input_arg))

    except AssertionError:
        raise AssertionError('Result of the command: {0}:{1} {2}contains '
                             'the value of the input argument: {3}:{4}'.format(
            res_storage_name,
            result,
            '' if negation else 'not ',
            input_arg_name,
            input_arg))