# coding: utf-8
"""
Created on 22.06.18
@author: Eugeny Kurkovich
"""

import uuid
from functools import reduce

from .consts import PlatformStore


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, attr.split('.'), obj)


def reverse_dict(d):
    return dict(zip(d.values(), d.keys()))


def remove_empty_values(obj):
    if isinstance(obj, dict):
        obj = dict(x for x in obj.items() if all(i is not None for i in x))
    elif isinstance(obj, (list, tuple)):
        obj = [x for x in obj if x is not None]
    return None or obj


def uniq_uuid():
    return str(uuid.uuid4().hex)[:16]


def serialize_data_store(obj):
    if isinstance(obj, PlatformStore):
        return obj._name
    return obj
