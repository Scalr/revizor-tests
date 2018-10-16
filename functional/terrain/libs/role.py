__author__ = 'gigimon'

import logging

from lettuce import world

from revizor2.backend import IMPL


LOG = logging.getLogger(__name__)


@world.absorb
def get_role(alias=None):
    """
    Return save Role object with setted database object and all staff
    :param str alias: Can be role alias or behavior
    :return: class:FarmRole
    """
    def find_role(alias):
        # NOTE: migrated
        LOG.debug('Find role with alias: %s' % alias)
        if not alias:
            role = getattr(world, '%s_role' % world.farm.roles[0].alias)
            return role
        for role in world.farm.roles:
            LOG.debug('Processing role: %s (%s) in farm' % (role.alias, role.id))
            if alias == role.alias or alias in role.role.behaviors:
                if hasattr(world, '%s_role' % role.alias):
                    return getattr(world, '%s_role' % role.alias)
                return role
    role = find_role(alias)
    if not role:
        world.farm.roles.reload()
        role = find_role(alias)
    assert role, 'Role with alias %s not found: %s' % (alias, role)
    return role


@world.absorb
def get_storage_device_by_mnt_point(mnt_point, role_alias=None):
    role = get_role(alias=role_alias)
    devices = IMPL.farm.get_role_settings(world.farm.id, role.role.id)['storages']
    device_config = filter(lambda x: x['mountPoint'] == mnt_point, devices['configs'])
    assert device_config, AssertionError('Can\'t found device for mount point: %s' % mnt_point)
    return devices['devices'][device_config[0]['id']]
