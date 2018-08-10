__author__ = 'gigimon'

import re
import logging

from lettuce import world

from revizor2.backend import IMPL

LOG = logging.getLogger(__name__)


@world.absorb
def bundle_task_created(server, bundle_id):
    contents = None
    for bundlelog in server.bundlelogs:
        if bundlelog.id == bundle_id:
            contents = bundlelog.contents
            break
    if contents:
        for log in contents:
            if 'Bundle task created' in log['message']:
                LOG.info('Bundle task for server %s was created with id: %s' % (server.id, bundle_id))
                return True
            elif 'Bundle task status changed to: failed' in log['message']:
                LOG.error('Bundle task for server %s with id: %s was failed with error: %s'
                            % (server.id, bundle_id, log['message']))
                raise AssertionError(log['message'])
    return AssertionError("Can't find bundle task for server %s" % server.id)


@world.absorb
def bundle_task_completed(server, bundle_id, *args, **kwargs):
    server.bundlelogs.reload()
    for bundlelog in server.bundlelogs:
        if bundlelog.id == bundle_id:
            contents = bundlelog.contents
            for log in contents:
                if 'Bundle task status: success' in log['message']:
                    for l in contents:
                        if 'Role ID:' in l['message']:
                            world.bundled_role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
                    LOG.info('Bundle task %s is complete. New role id: %s' % (bundle_id, world.bundled_role_id))
                    return True
                elif 'Bundle task status changed to: failed' in log['message']:
                    raise AssertionError(log['message'])
    return False


@world.absorb
def bundle_task_complete_rolebuilder(bundle_id):
    """
    Wait when bundletask will be finished (with success or failed status)
    """
    logs = IMPL.bundle.logs(bundle_id)
    for log in logs:
        if 'Bundle task status: success' in log['message']:
            return True
        elif 'Bundle task status changed to: failed' in log['message']:
            LOG.error('Bundle task with id: %s was failed with error: %s' % (bundle_id, log['message']))
            raise AssertionError(log['message'])
    return False

