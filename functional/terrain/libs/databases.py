__author__ = 'gigimon'

import logging

from lettuce import world

from revizor2.fixtures import resources
from revizor2.conf import CONF
from revizor2.consts import ServerStatus

LOG = logging.getLogger(__name__)
PLATFORM = CONF.feature.platform


@world.absorb
def wait_database(db_name, server):
    db_role = world.get_role()
    return db_role.db.database_exist(db_name, server)


@world.absorb
def wait_replication_status(behavior, status):
    db_status = world.farm.db_info(behavior)
    for server in db_status['servers']:
        if not db_status['servers'][server]['status'] == ServerStatus.RUNNING:
            LOG.warning('Server %s is not running it %s' % (db_status['servers'][server]['serverId'],
                                                            db_status['servers'][server]['status']))
            continue
        LOG.info("Check replication in server %s it is: %s" % (db_status['servers'][server]['serverId'],
                                                               db_status['servers'][server]['replication']['status']))
        if not db_status['servers'][server]['replication']['status'].strip() == status.strip():
            LOG.debug("Replication on server %s is %s" % (db_status['servers'][server]['serverId'],
                                                          db_status['servers'][server]['replication']['status']))
            return False
    return True


@world.absorb
def check_server_storage(serv_as, status):
    server = getattr(world, serv_as)
    volumes = server.get_volumes()
    LOG.debug('Volumes for server %s is: %s' % (server.id, volumes))
    if PLATFORM.is_ec2:
        storages = filter(lambda x: 'sda' not in x.extra['device'], volumes)
    elif PLATFORM.is_cloudstack:
        storages = filter(lambda x: x.extra['volume_type'] == 'DATADISK', volumes)
    if not storages and not status.strip() == 'deleted':
        raise AssertionError('Server %s not have storages' % server.id)
    if status.strip() == 'deleted' and len(storages) < len(getattr(world, '%s_storages' % serv_as)):
        return True
    for vol in volumes:
        if PLATFORM.is_ec2:
            state = 'used' if vol.extra['state'] in ['in-use', 'available'] else 'deleted'
        elif PLATFORM.is_cloudstack:
            state = 'used'
        if status == 'use' and state == 'used':
            return True
        elif status == 'deleted' and not state == 'deleted':
            return False
    return True


