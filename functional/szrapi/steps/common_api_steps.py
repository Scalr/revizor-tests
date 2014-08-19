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
    server = getattr(world, serv_as)
    # Get service api
    api = getattr(getattr(szrapi, service_api.strip())(server), command.strip())
    LOG.debug('Obtained %s instance %s for server %s' % (service_api, api, server.id))
    # Get api arguments
    args = None
    if isset_args:
        args = dict([key, templates[service_api][value.lower()] if value.isupper() else value] \
            for key,value in step.hashes[0].iteritems())
        setattr(world, 'api_args', args)
        LOG.debug('Obtained {0}.{1} extended arguments:\n{2}'.format(
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
        raise Exception('An error occurred while try to run: {0}.\n{1}'.format(
            command,
            e.message)
        )