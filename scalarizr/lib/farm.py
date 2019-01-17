import logging
import re
import time
import typing as tp

from revizor2 import CONF
from revizor2.api import Farm, IMPL, Role, FarmRole
from revizor2.consts import BEHAVIORS_ALIASES, DATABASE_BEHAVIORS
from revizor2.exceptions import NotFound
from revizor2.helpers import farmrole
from revizor2.helpers.roles import get_role_versions
from scalarizr.lib.defaults import Defaults

LOG = logging.getLogger(__name__)


def clear(farm: Farm):
    farm.roles.reload()
    if len(farm.roles):
        LOG.info('Clear farm roles')
        IMPL.farm.clear_roles(farm.id)
    farm.vhosts.reload()
    for vhost in farm.vhosts:
        LOG.info(f'Delete vhost: {vhost.name}')
        vhost.delete()
    try:
        farm.domains.reload()
        for domain in farm.domains:
            LOG.info(f'Delete domain: {domain.name}')
            domain.delete()
    except Exception:
        pass


def add_role_to_farm(context: dict,
                     farm: Farm,
                     behavior: str = None,
                     role: Role = None,
                     role_name: str = None,
                     role_options: tp.List[str] = None,
                     alias: str = None) -> FarmRole:
    behavior = (behavior or CONF.feature.behavior).strip()
    role_name = (role_name or '').strip()
    if role:
        role_id = role.id  #FIXME: Use Role object below
    else:
        role_id = CONF.feature.role_id or context.get(f'{role_name}_id', None)
    if role_options:
        LOG.debug(f'Additional role options: {role_options}')
    if role_id:
        if not isinstance(role_id, int) and not role_id.isdigit():
            raise AssertionError('Role environment variable can\'t be only in digit format')
        LOG.info(f'Get role by id: {role_id}')
        role = IMPL.role.get(role_id)
    else:
        role = get_role_by_behavior(behavior)
    if not role:
        raise NotFound('Role with id or by mask "%s" not found in Scalr' % (
                role_id or behavior))

    # world.wrt(etree.Element('meta', name='role', value=role['name']))
    # world.wrt(etree.Element('meta', name='dist', value=role['dist']))
    previously_added_roles = [r.id for r in farm.roles]

    alias = alias or role['name']
    LOG.info(f'Add role {role["id"]} with alias {alias} to farm')
    role_params = setup_farmrole_params(
        context,
        farm,
        role_options=role_options,
        alias=alias,
        behaviors=behavior)

    farm.add_role(role['id'], options=role_params.to_json())
    farm.roles.reload()
    added_role = [r for r in farm.roles if r.id not in previously_added_roles]

    if not added_role:
        raise AssertionError(f'Added role "{role["name"]}" not found in farm')
    LOG.debug(f'Save role object with name {added_role[0].alias}')
    context[f'{added_role[0].alias}_role'] = added_role[0]
    context[f'role_params_{added_role[0].id}'] = role_params
    return added_role[0]


def get_role_by_behavior(behavior) -> dict:
    behavior = BEHAVIORS_ALIASES.get(behavior, behavior)
    dist = CONF.feature.dist
    use_cloudinit_role = '-cloudinit' in behavior
    role_type = CONF.feature.role_type

    if use_cloudinit_role:
        dist_mask = dist.id
        role_ver_tpl = 'tmp-{beh}-{dist}-*-*'
        role_name_tpl = 'tmp-{beh}-{dist}-{ver}'
    else:
        dist_mask = dist.mask
        role_ver_tpl = '{beh}*-{dist}-{type}'
        role_name_tpl = '{beh}{ver}-{dist}-{type}'

    role_ver_mask = role_ver_tpl.format(
        beh=behavior,
        dist=dist_mask,
        type=role_type)
    LOG.info(f'Get role versions by mask: {role_ver_mask}')

    role_version = get_role_versions(role_ver_mask, use_latest=True)
    role_name = role_name_tpl.format(
        beh=behavior,
        dist=dist_mask,
        ver=role_version,
        type=role_type)
    LOG.info(f'Get role by name: {role_name}')
    roles = IMPL.role.list(dist=dist.dist, query=role_name)
    if roles:
        return roles[0]
    raise NotFound('Role with name: %s not found in Scalr' % role_name)


def setup_farmrole_params(context: dict,
                          farm: Farm,
                          role_options: tp.List[str] = None,
                          alias: str = None,
                          behaviors: tp.Union[str, tp.List[str]] = None,
                          setup_bundled_role: bool = False) -> farmrole.FarmRoleParams:
    platform = CONF.feature.platform
    dist = CONF.feature.dist
    behaviors = behaviors or []
    role_options = role_options or []
    role_params = farmrole.FarmRoleParams(platform, alias=alias)

    if isinstance(behaviors, str):
        behaviors = [behaviors]

    if not (setup_bundled_role and len(f'{farm.name}-{alias}') < 63):
        Defaults.set_hostname(role_params)

    for opt in role_options:
        LOG.info(f'Inspect role option: {opt}')
        if opt in ('branch_latest', 'branch_stable'):
            role_params.advanced.agent_update_repository = opt.split('_')[1]
        elif 'redis processes' in opt:
            redis_count = re.findall(r'(\d+) redis processes', opt)[0].strip()
            LOG.info(f'Setup {redis_count} redis processes')
            role_params.database.redis_processes = int(redis_count)
        elif 'chef-solo' in opt:
            Defaults.set_chef_solo(role_params, opt)
        else:
            Defaults.apply_option(role_params, opt)

    if not setup_bundled_role:
        if dist.is_windows:
            role_params.advanced.reboot_after_hostinit = True
        elif dist.id == 'scientific-6-x' or \
                (dist.id in ['centos-6-x', 'centos-7-x'] and platform.is_ec2):
            role_params.advanced.disable_iptables_mgmt = False

        if platform.is_ec2:
            role_params.global_variables.variables.append(
                role_params.global_variables,
                farmrole.Variable(
                    name='REVIZOR_TEST_ID',
                    value=context['test_id']
                )
            )
        if 'rabbitmq' in behaviors:
            role_params.network.hostname_template = ''

    if any(b in DATABASE_BEHAVIORS for b in behaviors):
        LOG.debug('Setup default db storages')
        Defaults.set_db_storage(role_params)
        if 'redis' in behaviors:
            LOG.info('Insert redis settings')
            snapshotting_type = CONF.feature.redis_snapshotting
            role_params.database.redis_persistence_type = snapshotting_type
            role_params.database.redis_use_password = True

    return role_params


def farm_launch_delayed(farm: Farm):
    """Start farm with delay for cloudstack"""
    if CONF.feature.platform.is_cloudstack:  # Maybe use on all cloudstack
        time.sleep(1800)
    farm.launch()
    LOG.info('Launch farm \'%s\' (%s)' % (farm.id, farm.name))
