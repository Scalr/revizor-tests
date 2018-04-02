__author__ = 'gigimon'
import time
import logging

from lettuce import world, step
from lxml import etree

from revizor2.api import Role, IMPL
from revizor2.conf import CONF
from revizor2.exceptions import NotFound
from revizor2.helpers import farmrole
from revizor2.utils import wait_until


LOG = logging.getLogger(__name__)


@step('I have a an empty running farm')
def having_empty_running_farm(step):
    """Clear and run farm and set to world.farm"""
    world.give_empty_farm(launched=True)


@step('I have a clean and stopped farm')
def having_a_stopped_farm(step):
    """Clear all roles from farm and stop farm"""
    world.give_empty_farm(launched=False)


@step(r"I add(?:\s(?P<behavior>[\w\d-]+))? role(?:\s(?P<role_name>[\w\d-]+))? to this farm(?:\swith\s(?P<role_options>[\w\d,-]+))?(?:\sas\s(?P<alias>[\w\d-]+))?")
def add_role_to_farm(step, behavior=None, role_name=None, role_options=None, alias=None):
    behavior = (behavior or CONF.feature.behavior).strip()
    role_name = (role_name or '').strip()
    role_id = CONF.feature.role_id or getattr(world, '%s_id' % role_name, None)
    if role_options:
        role_options = (o.strip() for o in role_options.strip().split(','))
    if role_id and role_id.isdigit():
        LOG.info("Get role by id: '%s'" % role_id)
        role = IMPL.role.get(role_id)
    else:
        role = world.get_role_by_mask(
            behavior,
            role_id)
    if not role:
        raise NotFound('Role with id or by mask "%s" not found in Scalr' % (
            role_id or behavior))

    world.wrt(etree.Element('meta', name='role', value=role['name']))
    world.wrt(etree.Element('meta', name='dist', value=role['dist']))
    previously_added_roles = [r.id for r in world.farm.roles]

    alias = alias or role['name']
    LOG.info('Add role %s with alias %s to farm' % (role['id'], alias))
    role_params = world.setup_farmrole_params(
        role_options=role_options,
        alias=alias,
        behaviors=behavior)

    world.farm.add_role(role['id'], options=role_params.to_json())
    world.farm.roles.reload()
    added_role = [r for r in world.farm.roles if r.id not in previously_added_roles]

    if not added_role:
        raise AssertionError('Added role "%s" not found in farm' % role['name'])
    LOG.debug('Save role object with name %s' % added_role[0].alias)
    setattr(world, '%s_role' % added_role[0].alias, added_role[0])
    setattr(world, 'role_params_%s' % added_role[0].id, role_params)


@step('I delete (\w+) role from this farm')
def delete_role_from_farm(step, role_type):
    LOG.info('Delete role %s from farm' % role_type)
    role = world.get_role(role_type)
    world.farm.delete_role(role.role_id)


@step('I (?:terminate|stop) farm')
def farm_terminate(step):
    """Terminate (stopping) farm"""
    world.farm.terminate()
    time.sleep(30)


@step('I start farm$')
def farm_launch(step):
    """Start farm"""
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I start farm with delay$')
def farm_launch(step):
    """Start farm with delay for cloudstack"""
    if CONF.feature.platform.is_cloudstack: #Maybe use on all cloudstack
        time.sleep(1800)
    world.farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (world.farm.id, world.farm.name))


@step('I add to farm imported role$')
def add_new_role_to_farm(step):
    bundled_role = Role.get(world.bundled_role_id)
    options = farmrole.FarmRoleParams(CONF.feature.platform, alias=bundled_role.name)
    world.farm.add_role(
        world.bundled_role_id,
        options=options.to_json())
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, '%s_role' % role.alias, role)


@step('I suspend farm')
def farm_state_suspend(step):
    """Suspend farm"""
    world.farm.suspend()


@step('I resume farm')
def farm_resume(step):
    """Resume farm"""
    world.farm.resume()


@step('I wait farm in ([\w]+) state')
def wait_for_farm_state(step, state):
    """Wait for state of farm"""
    wait_until(world.get_farm_state, args=(
        state, ), timeout=300, error_text=('Farm have no status %s' % state))
