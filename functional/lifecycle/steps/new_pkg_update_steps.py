# coding: utf-8

"""
Created on 09.01.2015
@author: Eugeny Kurkovich
"""

import logging

from lettuce import step, world
from revizor2.conf import CONF
from revizor2.api import IMPL, Server
from revizor2.consts import Platform, Dist
from revizor2.utils import wait_until
from revizor2.helpers import install_behaviors_on_node


LOG = logging.getLogger(__name__)

@step(r'I install scalarizr to the server from a branch ([A-za-z0-9\/\-\_]+)$')
def install_scalarizr(step, branch):
    pass

@step(r'I create image')
def create_image(step):
    pass


@step(r'I add image to the new role')
def create_role(step):
    pass


@step(r'I add created role to the farm with branch ([\w]+)$')
def setup_farm(step, branch):
    pass


@step(r'I trigger scalarizr update by Scalr UI')
def update_scalarizr_by_scalr_ui(step):
    pass


@step(r'^([\w\-]+) version is valid in ([\w\d]+)$')
def assert_version(step, service, serv_as):
    pass


@step(r'I fork ([A-za-z0-9\/\-\_]+) branch to ([A-za-z0-9\/\-\_]+)$')
def fark_git_branch(step, branch_from, branch_to):
    pass