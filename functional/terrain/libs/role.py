__author__ = 'gigimon'

from lettuce import world


@world.absorb
def get_role(alias=None):
    """
    Return save Role object with setted database object and all staff
    :param str alias: Can be role alias or behavior
    :return: class:FarmRole
    """
    world.farm.roles.reload()
    if not alias:
        return getattr(world, '%s_role' % world.farm.roles[0].alias)
    for role in world.farm.roles:
        if alias == role.alias or alias in role.role.behaviors:
            return getattr(world, '%s_role' % role.alias)