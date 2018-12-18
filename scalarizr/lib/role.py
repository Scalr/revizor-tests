import logging
import typing as tp
from datetime import datetime

from libcloud.compute.base import NodeImage

from revizor2.conf import CONF
from revizor2.api import Farm, FarmRole, Role
from revizor2.backend import IMPL
from revizor2.helpers import farmrole

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


def create_role(image: NodeImage,
                behaviors: tp.List[str] = None,
                non_scalarized: bool = False,
                has_cloudinit: bool = True) -> dict:
    behaviors = behaviors or ['chef']
    if CONF.feature.dist.id == 'coreos':
        behaviors = ['base']
    platform = CONF.feature.platform

    if platform.is_gce:
        cloud_location = ""
        image_id = image.extra['selfLink'].split('projects')[-1][1:]
    elif platform.is_azure:
        cloud_location = platform.location
        image_id = '/'.join(image.name.split(' ')[:-1]) + '/latest'
    else:
        cloud_location = platform.location
        image_id = image.id

    image_kwargs = dict(
        platform=platform.name,
        cloud_location=cloud_location,
        image_id=image_id
    )
    if platform.is_azure:
        image_kwargs['cloud_location'] = ""
    name = 'tmp-{}-{}-{:%d%m%Y-%H%M%S}'.format(
        ''.join(behaviors),
        CONF.feature.dist.id,
        datetime.now())
    # Checking an image
    LOG.debug('Checking an image {image_id}:{platform}({cloud_location})'.format(**image_kwargs))
    image_registered = False
    try:
        image_check_result = IMPL.image.check(**image_kwargs)
    except Exception as e:
        if not ('Image has already been registered' in str(e)):
            raise
        image_registered = True
    if not image_registered:
        # Register image to the Scalr
        LOG.debug('Register image %s to the Scalr' % name)
        image_kwargs.update(dict(
            software=behaviors,
            name=name,
            is_scalarized=not non_scalarized,
            has_cloudinit=has_cloudinit,
            image_volumes=image_check_result.get('volumes', None)))
        image = IMPL.image.create(**image_kwargs)
    else:
        image = IMPL.image.get(image_id=image_id)
    role_kwargs = dict(
        name=name[:50].strip('-'),
        is_scalarized=int(not non_scalarized or has_cloudinit),
        behaviors=behaviors,
        images=[dict(
            platform=platform.name,
            cloudLocation=cloud_location,
            hash=image['hash'])])
    LOG.debug('Create new role {name}. Role options: {behaviors} {images}'.format(**role_kwargs))
    role = IMPL.role.create(**role_kwargs)
    return role


def change_branch_in_farm_role(farm_role: FarmRole, branch: str = None):
    """Change branch for selected role"""
    branch = branch or ''
    if 'system' in branch:
        branch = CONF.feature.branch
    elif not branch.strip():
        branch = CONF.feature.to_branch
    else:
        branch = branch.strip()
    LOG.info(f'Change branch to {branch} for role {farm_role.name}')
    role_options = {farmrole.DevelopmentGroup.scalarizr_branch.name: branch,
                    farmrole.DevelopmentGroup.scalarizr_repo.name: CONF.feature.ci_repo}
    farm_role.edit(options=role_options)
