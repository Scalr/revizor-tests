import logging

from revizor2.api import Farm, FarmRole
from revizor2.backend import IMPL

LOG = logging.getLogger(__name__)


def get_role(context: dict, farm: Farm, alias: str = None) -> FarmRole:
    """
    Return save Role object with setted database object and all staff
    """

    def find_role(name):
        LOG.debug('Find role with alias: %s' % name)
        if not name:
            return context['%s_role' % farm.roles[0].alias]
        for r in farm.roles:
            LOG.debug('Processing role: %s (%s) in farm' % (r.alias, r.id))
            if name == r.alias or name in r.role.behaviors:
                if '%s_role' % r.alias in context:
                    return context['%s_role' % r.alias]
                return r

    role = find_role(alias)
    if not role:
        farm.roles.reload()
        role = find_role(alias)
    assert role, 'Role with alias %s not found: %s' % (alias, role)
    return role


def get_storage_device_by_mnt_point(context: dict, farm: Farm, mnt_point: str, role_alias: str = None):
    role = get_role(context, farm, alias=role_alias)
    devices = IMPL.farm.get_role_settings(farm.id, role.role.id)['storages']
    device_config = next(filter(lambda x: x['mountPoint'] == mnt_point, devices['configs']))
    return devices['devices'][device_config['id']]
