# coding: utf-8
"""
Created on 22.06.18
@author: Eugeny Kurkovich
"""

from string import Formatter
from functools import reduce

from box import Box


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, attr.split('.'), obj)


class UnexpectedSchemasFormat(Exception):
    pass


class RequestSchemaFormatter(Box):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def schema_from_json(cls, json_data, **kwargs):
        box_obj = super(RequestSchemaFormatter, cls).from_json(json_data, **kwargs)
        if not rgetattr(box_obj, 'endpoint.path', None):
            raise UnexpectedSchemasFormat('Not enough actual fields on request schema')
        box_obj.endpoint.params = {
            placeholder: None
            for _, placeholder, _, _ in Formatter().parse(box_obj.endpoint.path)
            if placeholder
        }
        box_obj.params = {}
        box_obj.body = {}
        return box_obj


