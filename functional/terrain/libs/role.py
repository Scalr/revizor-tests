__author__ = 'gigimon'

from lettuce import world


@world.absorb
def get_role(alias=None):
    """
    Return save Role object with setted database object and all staff
    :param str alias: Can be role alias or behavior
    :return: class:FarmRole
    """
    def find_role(alias):
        if not alias:
            return getattr(world, '%s_role' % world.farm.roles[0].alias)
        for role in world.farm.roles:
            if alias == role.alias or alias in role.role.behaviors:
                return getattr(world, '%s_role' % role.alias)
    role = find_role(alias)
    if not role:
        world.farm.roles.reload()
        role = find_role(alias)
    assert role, 'Role with alias %s not found' % alias
    return role