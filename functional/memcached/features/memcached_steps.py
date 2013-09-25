# coding: utf-8

'''
Created on 09.24.2013
@author: Eugeny Kurkovich
'''

import mapping
from lettuce import world, step
from memcache import Client
from common import LOG



@step('I have connected memcache client to ([\w\d]+)$')
def i_initialize_instance(step, serv_as):
    world.memcache_maps = mapping.memcached
    world.memcache_client = Client(['%s:%s' % (getattr(world, serv_as), world.memcache_maps["port"])], debug=0)

@step('I run a "(.*)" to "(.*)" for new item on ([\w\d]+)$')
def i_add_new_item(step, comands, comand, serv_as):
    assert getattr(world.memcache_client, world.memcache_maps[comands][comand])('test_key', 'test_value'), \
        LOG.debug("No element was added to the stack memcache on %s" % getattr(world, serv_as))





