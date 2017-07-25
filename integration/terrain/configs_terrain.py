import os

from lettuce import world, step, after

from revizor2.conf import CONF


@step('I have configured revizor environment:')
def configure_revizor(step):
    for revizor_opt in step.hashes:
        os.environ['RV_%s' % revizor_opt['name'].upper()] = revizor_opt['value']
        CONF.feature[revizor_opt['name']] = revizor_opt['value']


