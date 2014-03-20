__author__ = 'gigimon'

import logging

from lettuce import world


LOG = logging.getLogger(__name__)


@world.absorb
def get_role(alias=None):
    """
    Return save Role object with setted database object and all staff
    :param str alias: Can be role alias or behavior
    :return: class:FarmRole
    """
    def find_role(alias):
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