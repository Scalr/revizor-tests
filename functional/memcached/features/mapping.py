# coding: utf-8
'''
Created on 09.24.2013
@author: Eugeny Kurkovich
'''

""" Clients of memcached communicate with server through TCP connections protcol """

memcached = {
    "port": "11211",
    "memcached_comand": {
        "get key": "get",
        "set key": "set",
        "add newkey": "add",
        "replace key": "replace",
        "prepend key": "prepend",
        "incr key": "incr",
        "decr key": "decr",
        "delete key": "delete",
        "Server version": "version",
        "quit": "quit"
    }
}
