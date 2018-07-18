# coding: utf-8
"""
Created on 22.06.18
@author: Eugeny Kurkovich
"""
import uuid
from functools import reduce


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, attr.split('.'), obj)


def reverse_dict(d):
    return dict(zip(d.values(), d.keys()))


def remove_empty_values(obj):
    if isinstance(obj, dict):
        obj = dict(x for x in obj.items() if all(x))
    elif isinstance(obj, (list, tuple)):
        obj = [x for x in obj if x]
    return None or obj


def uniq_uuid():
    return str(uuid.uuid4().hex)[:16]


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
