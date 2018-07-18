# coding: utf-8
"""
Created on 09.07.18
@author: Eugeny Kurkovich
"""


class BaseException(Exception):
    pass


class UnexpectedSchemasFormat(BaseException):
    pass


class ResponseValidationError(BaseException):
    pass


class FileNotFoundError(BaseException):
    pass


class PathNotFoundError(BaseException):
    pass
