# coding: utf-8

"""
Created on 08.18.2014
@author: Eugeny Kurkovich
"""

import logging
from lettuce import world, step

LOG = logging.getLogger('Apache api steps')


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