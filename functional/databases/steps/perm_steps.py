import time

from lettuce import world, step

from revizor2.fixtures import resources
from revizor2.cloud import Cloud
import logging


LOG = logging.getLogger('permissions')

@step('Then I install ([\w]+) client to ([\w\d]+)')
def prepare_environment(step, env, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Upload database test script')
    node.put_file('/root/check_db.py',
                  resources('scripts/check_db.py').get())
    LOG.info('Launch database test script for update environment')
    node.run('python /root/check_db.py --db=%s' % env)


