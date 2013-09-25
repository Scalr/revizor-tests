# coding: utf-8

'''
Created on 09.24.2013
@author: Eugeny Kurkovich
'''

from mapping import memcached
from lettuce import world, step
from memcache import Client

@step('I have a connected "(.*)" client to ([\w\d]+)$')
def i_initialize_instance(step, maps, serv_as):
    world.memcache_maps = maps
    world.memcache_client = Client(['%s:%s' % (getattr(world, serv_as), world.memcache_maps["port"])], debug=0)

@step('I run a "(.*)" to "(.*)" for new item')
def i_add_new_item(step, comands, comand):
    comands = world.memcache_maps[comands]
    assert world.memcache_client.comands[comand]('test_key','test_value'), \
       "No element was added to the stack memcache server!"





