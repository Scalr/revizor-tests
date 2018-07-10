# coding: utf-8
"""
Created on 22.06.18
@author: Eugeny Kurkovich
"""

from functools import reduce


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, attr.split('.'), obj)


def reverse_dict(d):
    return dict(zip(d.values(), d.keys()))


class Defaults(object):

    request_types = {
        'create': 'post',
        'delete': 'delete',
        'edit': 'patch',
        'list': 'get',
        'get': 'get'
    }

    response_data_types = {
        'string': '',
        'boolean': True,
        'integer': 1,
        'number': 1,
        'array': []
    }
