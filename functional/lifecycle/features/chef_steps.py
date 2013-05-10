import os
import logging

from lettuce import world, step

from revizor2.cloud import Cloud


LOG = logging.getLogger('chef')

@step('I add role to this farm with chef settings')
def having_role_in_farm(step):
    role_type = os.environ.get('RV_BEHAVIOR', 'base')
    role = world.add_role_to_farm(role_type=role_type,
                                  options={"chef.bootstrap": 1,
                                           "chef.runlist_id": "143",
                                           "chef.attributes": '{"memcached":{"memory":"1024"}}',
                                           "chef.server_id": "3",
                                           "chef.environment": "_default",
                                           "chef.role_name": None,
                                           "chef.node_name_tpl": "",
                                           })
    LOG.info('Add role to farm %s' % role)
    world.role_type = role_type
    if not role:
        raise AssertionError('Error in add role to farm')
    setattr(world, world.role_type + '_role', role)
    world.role = role


@step("And process '([\w]+)' has options '(.+)' in (.+)")
def check_process_options(step, process, options, serv_as):
    server = getattr(world, serv_as)
    LOG.debug('Want check process %s and options %s' % (process, options))
    c = Cloud()
    node = c.get_node(server)
    out = node.run('ps aux | grep %s' % process)
    LOG.debug('Grep for ps aux: %s' % out[0])
    for line in out[0].splitlines():
        if not line.split()[10].startswith('/'):
            continue
        LOG.info('Work with line: %s' % line)
        if not options in ' '.join(line.split()[10:]):
            raise AssertionError('Options %s not in process, %s' % (options, ' '.join(line.split()[10:])))
        else:
            return True
    raise AssertionError('Not found process: %s' % process)
