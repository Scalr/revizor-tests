import time
import logging
from datetime import datetime

from lettuce import world

from revizor2.api import Farm, IMPL
from revizor2.conf import CONF
from revizor2.fixtures import tables
from revizor2.consts import BEHAVIORS_ALIASES
from revizor2.exceptions import NotFound
from revizor2.helpers import farmrole
from revizor2.helpers.roles import get_role_versions

from lxml import etree

LOG = logging.getLogger(__name__)


@world.absorb
def give_empty_farm(launched=False):
    if CONF.main.farm_id is None:
        LOG.info('Farm ID not setted, create a new farm for test')
        world.farm = Farm.create('tmprev-%s' % datetime.now().strftime('%d%m%H%M%f'),
                                 "Revizor farm for tests\n"
                                 "RV_BRANCH={}\n"
                                 "RV_PLATFORM={}\n"
                                 "RV_DIST={}\n".format(
                                     CONF.feature.branch,
                                     CONF.feature.platform.name,
                                     CONF.feature.dist.dist
                                 ))
        CONF.main.farm_id = world.farm.id
    else:
        LOG.info('Farm ID is setted in config use it: %s' % CONF.main.farm_id)
        world.farm = Farm.get(CONF.main.farm_id)
    world.farm.roles.reload()
    if len(world.farm.roles):
        LOG.info('Clear farm roles')
        IMPL.farm.clear_roles(world.farm.id)
    world.farm.vhosts.reload()
    for vhost in world.farm.vhosts:
        LOG.info('Delete vhost: %s' % vhost.name)
        vhost.delete()
    try:
        world.farm.domains.reload()
        for domain in world.farm.domains:
            LOG.info('Delete domain: %s' % domain.name)
            domain.delete()
    except Exception:
        pass
    if world.farm.terminated and launched:
        world.farm.launch()
    elif world.farm.running and not launched:
        world.farm.terminate()
    LOG.info('Return empty running farm: %s' % world.farm.id)


@world.absorb
def add_role_to_farm(behavior, options, role_id=None):
    """
    Insert role to farm by behavior and find role in Scalr by generated name.
    Role name generate by the following format:
    {behavior}{RV_ROLE_VERSION}-{RV_DIST}-{RV_ROLE_TYPE}
    Moreover if we setup environment variable RV_ROLE_ID it added role with this ID (not by name)
    """
    platform = CONF.feature.platform
    #FIXME: Rewrite this ugly and return RV_ROLE_VERSION
    def get_role(behavior, dist=None):
        if CONF.feature.role_type == 'shared':
            #TODO: Try get from Scalr
            role = tables('roles-shared').filter(
                {'dist': CONF.feature.dist.id,
                 'behavior': behavior,
                 'platform': platform.name}).first()
            role = IMPL.role.get(role.keys()[0])
        else:
            if behavior in BEHAVIORS_ALIASES:
                behavior = BEHAVIORS_ALIASES[behavior]
            if '-cloudinit' in behavior:
                mask = 'tmp-%s-%s-*-*' % (behavior, CONF.feature.dist.id)
            else:
                if CONF.feature.role_type == 'instance':
                    mask = '%s*-%s-%s-instance' % (behavior, dist, CONF.feature.role_type)
                else:
                    mask = '%s*-%s-%s' % (behavior, dist, CONF.feature.role_type)
            LOG.info('Get role versions by mask: %s' % mask)
            versions = get_role_versions(mask)
            versions.sort()
            versions.reverse()
            #TODO: Return RV_ROLE_VERSION
            if CONF.feature.role_type == 'instance':
                role_name = '%s%s-%s-%s-instance' % (
                    behavior, versions[0],
                    dist, CONF.feature.role_type)
            elif '-cloudinit' in behavior:
                role_name = 'tmp-%s-%s-%s' % (behavior, CONF.feature.dist.id, versions[0])
            else:
                role_name = '%s%s-%s-%s' % (
                    behavior, versions[0],
                    dist, CONF.feature.role_type)
            LOG.info('Get role by name: %s' % role_name)
            roles = IMPL.role.list(query=role_name)
            if not roles:
                raise NotFound('Role with name: %s not found in Scalr' % role_name)
            role = roles[0]
        return role
    # WORKAROUND!
    dist = CONF.feature.dist.mask
    if CONF.feature.role_id:
        LOG.info("Get role by id: '%s'" % CONF.feature.role_id)
        if CONF.feature.role_id.isdigit():
            role = IMPL.role.get(CONF.feature.role_id)
        else:
            roles = IMPL.role.list(query=CONF.feature.role_id)
            if roles:
                role = roles[0]
        if not behavior in role['behaviors']: #TODO: Think about role id and behavior
            LOG.warning('Behavior %s not in role behaviors %s' % (behavior, role['behaviors']))
            role = get_role(behavior, role['dist'])
        if not role:
            raise NotFound('Role with id %s not found in Scalr, please check' % CONF.feature.role_id)
    else:
        if not role_id:
            role = get_role(behavior, dist)
        else:
            role = IMPL.role.get(role_id)
    world.wrt(etree.Element('meta', name='role', value=role['name']))
    world.wrt(etree.Element('meta', name='dist', value=role['dist']))
    old_roles_id = [r.id for r in world.farm.roles]
    options.alias = options.alias or role['name']
    LOG.info('Add role %s with alias %s to farm' % (role['id'], options.alias))
    if dist in ('windows-2008', 'windows-2012') and platform.is_azure:
        LOG.debug('Dist is windows, set instance type')
        options.instance_type = 'Standard_A1'
    if platform.is_ec2:
        options.global_variables.variables.append(
            options.global_variables,
            farmrole.Variable(
                name='REVIZOR_TEST_ID',
                value=getattr(world, 'test_id')
            )
        )
    setattr(world, 'last-role-params', options)
    world.farm.add_role(role['id'], options=options.to_json())
    time.sleep(3)
    world.farm.roles.reload()
    new_role = [r for r in world.farm.roles if r.id not in old_roles_id]
    if not new_role:
        raise AssertionError('Added role "%s" not found in farm' % role['name'])
    return new_role[0]


@world.absorb
def get_farm_state(state):
    world.farm = Farm.get(world.farm.id)
    if world.farm.status == state:
        return True
    else:
        raise AssertionError('Farm is Not in %s state' % state)