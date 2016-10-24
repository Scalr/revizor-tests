import logging

from lettuce import world, step

LOG = logging.getLogger(__name__)


@step('I check that cloudinit is installed')
def check_cloudinit(step):
    node = getattr(world, 'cloud_server')
    out = node.run('cloud-init -v')[2]
    if out != 0:
        raise AssertionError('Cloud-init is not installed!')
