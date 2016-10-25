import logging

from lettuce import world, step

LOG = logging.getLogger(__name__)


@step('I check that cloudinit is installed')
def check_cloudinit(step):
    node = getattr(world, 'cloud_server')
    out = node.run('cloud-init -v')[2]
    if out != 0:
        raise AssertionError('Cloud-init is not installed!')


@step("I rebundle ([\w]+)")
def rebundle_server(step, serv_as):
    step.behave_as("""
        When I create server snapshot for {serv_as}
        Then Bundle task created for {serv_as}
        And Bundle task becomes completed for {serv_as}
        """.format(serv_as=serv_as))
