# coding: utf-8

'''
Created on 09.24.2013
@author: Eugeny Kurkovich
'''
import logging

import mapping
from lettuce import world, step
from memcache import Client


LOG = logging.getLogger(__name__)


@step('I initialize instance memcache Client on ([\w\d]+)$')
def initialize_memcached_instance(step, serv_as):
    """Initialization instance memcache Client class"""
    world.memcache_maps = mapping.memcached
    world.memcache_client = Client(['%s:%s' % (getattr(world, serv_as).public_ip, world.memcache_maps["port"])], debug=0)


@step('I run a "(.*)" to "(.*)" for new item on ([\w\d]+)$')
def add_new_item_to_memcached(step, commands, command, serv_as):
    """Add new item to memcache server (dict,str)"""
    result = getattr(world.memcache_client, world.memcache_maps[commands][command])('1000','test_value')
    LOG.debug('Result of command %s from memcache client is %s' % (command, result))
    if not result:
        raise AssertionError('Suggested command is not added an element to memcache: world.memcache_client.%s' % str(world.memcache_maps[commands][command])+"('1000','test_value')")


@step('I run a "(.*)" to "(.*)" from item on ([\w\d]+)$')
def get_item_from_memcached(step, commands, command, serv_as):
    """Get item from memcache server  for the key (dict,str)"""
    result = getattr(world.memcache_client, world.memcache_maps[commands][command])('1000')
    LOG.debug('Result of command %s from memcache client is %s' % (command, result))
    if result != "test_value":
        raise AssertionError('Suggested command is not get element from memcache: world.memcache_client.%s' % str(world.memcache_maps[commands][command])+"('1000')")
