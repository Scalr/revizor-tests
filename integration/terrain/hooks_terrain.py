import sys
import logging

from lettuce import world, after, before

from revizor2.conf import CONF


LOG = logging.getLogger(__name__)


@before.all
def prepare_env():
    if CONF.scalr.branch is None and CONF.scalr.te_id is None:
        print('Please define RV_TE_ID or RV_SCALR_BRANCH for tests')
        sys.exit(1)
    world.files = {}


@after.all
def destroy_container(total):
    if (not total.steps_failed and CONF.feature.stop_farm) or (CONF.feature.stop_farm and CONF.scalr.te_id):
        LOG.info('Destroy testenv because all fine')
        world.testenv.destroy()
    else:
        LOG.warning('Container %s can\'t be destroyed because test failed :(' % world.testenv.te_id)
