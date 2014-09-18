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
    LOG.debug('Set %s instance %s for server %s' % (service_api, api, server.id))
    # Get api arguments
    args = {}
    if isset_args:
        for key, value in step.hashes[0].iteritems():
            try:
                if value.isupper():
                    args.update({key: templates[service_api][value.lower()]})
                else:
                    args.update({key: eval(value)})
            except Exception:
                args.update({key: value})

        # Save api args to world [command_name]_args
        setattr(world, ''.join((command, '_args')), args)
        LOG.debug('Save {0}.{1} extended arguments: {2}'.format(
            service_api,
            command,
            args
        ))
    # Run api command
    try:
        api_result = api(**args) if args else api()
        LOG.debug('Run %s instance method %s.' % (service_api, command))
        # Save api command result to world [command_name]_res
        setattr(world, ''.join((command, '_res')), api_result)
        LOG.debug('Save {0} instance method {1} result: {2}'.format(
            service_api,
            command,
            api_result))
    except Exception as e:
        raise Exception('An error occurred while try to run: {0}.\nScalarizr api Error: {1}'.format(
            command,
            e.message)
        )


@step(r'api result (\"\w+\") (does not\s)?contain argument (\"\w+\")(?:\sfrom command\s("\w+\"))?')
def assert_api_result(step, res_storage_name, negation, input_arg_name, args_storage_name):

    """
        :param res_storage_name: attribute name in world stored api result
        :param negation: negation
        :param input_arg_name: attribute name in world stored api input arguments
        :param args_storage_name:
    """

    # Get api command input args storage
    storage_name = ''.join((args_storage_name.replace('"', ''), '_args')) if args_storage_name \
        else ''.join((res_storage_name.strip().replace('"', ''), '_args'))

    # Get api command input argument
    input_arg = getattr(world, storage_name)[input_arg_name.strip().replace('"', '')]
    LOG.debug('Obtained api command {0} input argument {1}: {2}'.format(
        res_storage_name if not args_storage_name else args_storage_name.split(' ')[-1],
        input_arg_name,
        input_arg))

    # Get api command result
    api_result = getattr(world, ''.join((res_storage_name.strip().replace('"', ''), '_res')))
    LOG.debug('Obtained api command {0} result: {1}'.format(
        res_storage_name,
        api_result))

    # Check api command result
    try:
        if isinstance(api_result, (list, tuple)):
            assert all(input_arg not in res for res in api_result) if negation \
                else any(input_arg in res for res in api_result)
        elif isinstance(api_result, str):
            assert (input_arg not in api_result) if negation \
                else (input_arg in api_result)
        LOG.debug('Result of the command: {0}:{1} {2}contains '
                  'the value of the input argument: {3}:{4}'.format(
                  res_storage_name,
                  api_result,
                  'not ' if negation else '',
                  input_arg_name,
                  input_arg))

    except AssertionError:
        raise AssertionError('Result of the command: {0}:{1} {2}contains '
                             'the value of the input argument: {3}:{4}'.format(
                             res_storage_name,
                             api_result,
                             '' if negation else 'not ',
                             input_arg_name,
                             input_arg))


@step(r'api result (\"\w+\") has (\"\w+\") data')
def assert_api_result_data(step, res_storage_name, data):

     # Get api command result
    api_result = getattr(world, ''.join((res_storage_name.strip().replace('"', ''), '_res')))
    LOG.debug('Obtained api command {0} result: {1}'.format(
        res_storage_name,
        api_result))
    # Assert api result
    data = data.strip().replace('"', '')
    try:
        if isinstance(api_result, dict):
            assertion_data = api_result.get(data, False)
            LOG.debug('Obtained api command {0} assertion data: {1}'.format(
                res_storage_name,
                assertion_data))
            assert assertion_data
            LOG.debug('Api command {0} result has assertion key: {1} data: {2}'.format(
                res_storage_name,
                data,
                assertion_data
            ))
        elif isinstance(api_result, (list, tuple)):
            pass
        elif isinstance(api_result, str):
            LOG.debug('Obtained api command {0} assertion data: {1}'.format(
                res_storage_name,
                data))
            assert data in api_result
            LOG.debug('Api command {0} result has assertion data: {1}'.format(
                res_storage_name,
                data
            ))
    except AssertionError:
        raise AssertionError('Api command {0} result has not assertion data: {1}'.format(
                res_storage_name,
                data
            ))