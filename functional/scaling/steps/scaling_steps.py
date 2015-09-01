__author__ = '<Oleg Suharev oleg@scalr.com>'
import logging

from lettuce import world, step

from revizor2.conf import CONF

LOG = logging.getLogger(__name__)


@step(r"I set file '([\w/\._:\\]+)' content to (\d+) on ([\w\d]+)")
def set_file_content(step, filename, content, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Set content "%s" to file "%s"' % (content, filename))
    if CONF.feature.dist.startswith('win'):
        world.run_cmd_command(server, 'echo %s > %s' % (content, filename))
    else:
        node = world.cloud.get_node(server)
        node.run('echo %s > %s' % (content, filename))