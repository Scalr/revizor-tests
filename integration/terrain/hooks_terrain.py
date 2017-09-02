import sys

from lettuce import world, step, after, before

from revizor2.conf import CONF


@before.all
def prepare_env():
    if CONF.scalr.branch is None and CONF.scalr.te_id is None:
        print('Please define RV_TE_ID or RV_SCALR_BRANCH for tests')
        sys.exit(1)
    world.files = {}
