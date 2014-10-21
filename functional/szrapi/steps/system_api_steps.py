# coding: utf-8

"""
Created on 10.14.2014
@author: Eugeny Kurkovich
"""

import logging
import base64
from lettuce import world, step
from revizor2 import szrapi

LOG = logging.getLogger(__name__)


@step(r'I get script result by (\"[\w\s]+\") command (\"[\w\S\s]+\") on ([\w\d]+)')
def get_scripting_result_by_api(step, service_api, command, serv_as):
    # Set attributes
    server = getattr(world, serv_as)
    service_api = service_api.strip().replace('"', '')
    command = command.strip().replace('"', '')
    # Get service api
    api = getattr(getattr(szrapi, service_api)(server), command)
    LOG.debug('Set %s instance %s for server %s' % (service_api, api, server.id))
    # Run api command
    script_id = [script_log.execution_id for script_log in server.scriptlogs if script_log.event == 'Manual'][0]
    LOG.debug('Obtained id by executed script: %s' % script_id)
    try:
        api_result = api(exec_script_id=script_id, maxsize=4096)['stdout']
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


@step(r'api result (\"[\w\S\s]+\") has (\"[\w\S\s]+\") logging data')
def assert_logs(step, res_storage_name, data=None):
    logs = {
        'get_debug_log': 'scalarizr_debug.log',
        'get_update_log': 'scalarizr_update.log',
        'get_log': 'scalarizr.log',
        'get_script_logs': 'Linux ping-pong.log'
    }
    storage = res_storage_name.strip().replace('"', '')
    data = data.strip().replace('"', '')
     # Get api command result
    api_result = base64.decodestring(getattr(world, ''.join((storage, '_res'))))
    LOG.debug('Obtained api command {0} result: {1}'.format(
        storage,
        api_result))
    # Assert api result
    assertion_message = '{0} has not assertion data: {1}'.format(
        logs[storage],
        data)
    assert api_result.find(data, 0, 512) >= 0, assertion_message
    LOG.debug('{0} has assertion data: {1}'.format(
        logs[storage],
        data))