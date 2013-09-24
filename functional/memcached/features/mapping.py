# coding: utf-8
'''
Created on 09.24.2013
@author: Eugeny Kurkovich
'''

""" Clients of memcached communicate with server through TCP connections protcol """

memcached_mapping = {
    "port" : "11211",
    "memcached_command" : {
        "get" : "get key",
        "set" : "set key",
        "add" : "add newkey",
        "replace" : "replace key",
        "prepend" : "prepend key",
        "incr" : "incr key",
        "decr" : "decr key",
        "delete" : "delete key",
        "stats" : {
            "stats" :"Prints general statistics",
            "stats slabs" :"Prints memory statistics",
            "stats malloc" : "Prints memory statistics",
            "stats items" : "Print higher level allocation statistics",
            "stats detail" : "",
            "stats sizes" : "",
            "stats reset" : ""

        },
        "version" : "Prints server version",
        "quit" : "quit"

    }
}
