# coding: utf-8
"""
Created on 05.06.18
@author: Eugeny Kurkovich
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--ev", "--ext_validation", dest="ext_validation", action="store_true",
        help="Set default behavior of validation util, if 'False' api response not validate by flex"
    )


pytest_plugins = [
    "api.plugins.filefixture",
    "api.utils.app_session"
]
