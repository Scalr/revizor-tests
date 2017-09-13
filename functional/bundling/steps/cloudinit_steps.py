import logging

from lettuce import world, step, before
from revizor2.api import Dist, CONF

LOG = logging.getLogger(__name__)


@before.each_scenario
def remove_unsupported_behaviors(scenario):
    if scenario.name == "Check roles and rebundle":
        if CONF.feature.dist.id == 'centos-7-x':
            scenario.outlines.remove({'behavior': 'mysql2'})
        elif CONF.feature.dist.id == 'ubuntu-16-04':
            scenario.outlines.remove({'behavior': 'mysql2'})
            scenario.outlines.remove({'behavior': 'percona'})
        elif CONF.feature.dist.id == 'coreos':
            scenario.outlines = [{'behavior': 'base'}]
    elif CONF.feature.dist.id == 'coreos' and scenario.name == "Create test roles with cloudinit":
        scenario.outlines = [{'behavior_set': 'base'}]


@step(r"I check that cloudinit is installed")
def check_cloudinit(step):
    node = getattr(world, 'cloud_server')
    cmd = 'coreos-cloudinit --version' if CONF.feature.dist.id == 'coreos' else 'cloud-init -v'
    out = node.run(cmd)[2]
    if out != 0:
        if CONF.feature.dist.is_centos:
            node.run('yum -y install cloud-init')
        else:
            node.run('sudo apt-get install cloud-init -y')
        out = node.run('cloud-init -v')[2]
        if out != 0:
            raise AssertionError('Cloud-init is not installed!')


@step(r"I rebundle ([\w]+)")
def rebundle_server(step, serv_as):
    step.behave_as("""
        When I create server snapshot for {serv_as}
        Then Bundle task created for {serv_as}
        And Bundle task becomes completed for {serv_as}
        """.format(serv_as=serv_as))
