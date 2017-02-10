import logging

from lettuce import world, step
from revizor2.api import Dist, CONF

LOG = logging.getLogger(__name__)


@step(r"I check that cloudinit is installed")
def check_cloudinit(step):
    #TODO: Add support for centos6
    node = getattr(world, 'cloud_server')
    out = node.run('cloud-init -v')[2]
    if out != 0:
        if CONF.feature.dist.is_centos:
            node.run('yum install cloud-init -y')
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
