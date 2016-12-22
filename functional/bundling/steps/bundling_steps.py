import logging
from datetime import datetime

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.api import Farm, Role, IMPL
from revizor2.consts import Platform, Dist
from revizor2.utils import wait_until


LOG = logging.getLogger(__name__)


# @step('I add to farm role created by last bundle task')
# def add_new_role_to_farm(step):
#     bundled_role = Role.get(world.bundled_role_id)
#     world.farm.add_role(world.bundled_role_id)
#     world.farm.roles.reload()
#     role = world.farm.roles[0]
#     setattr(world, bundled_role.behaviors_as_string() + '_role', role)


@step('I create server snapshot for ([\w]+) via scalarizr api$')
def rebundle_server_via_api(step, serv_as):
    """Start rebundle for server via scalarizr api"""
    server = getattr(world, serv_as)
    operation_id = None
    name = 'tmp-%s-%s' % (server.role.name, datetime.now().strftime('%m%d%H%M'))
    setattr(world, 'last_bundle_role_name', name)
    LOG.info('Create image via scalarizr api from server %s and image name %s' % (server.id, name))

    if CONF.feature.driver.current_cloud in (Platform.EC2, Platform.GCE)\
            and not CONF.feature.dist.is_windows\
            and not CONF.feature.dist.startswith('rhel')\
            or (CONF.feature.driver.current_cloud == Platform.GCE
                and CONF.feature.dist.startswith('rhel')):
        LOG.info('Image creation in this platform doing in one step')
        operation_id = server.api.image.create(name=name, async=True)
        LOG.info('Image creation operation_id - %s' % operation_id)

        if not operation_id:
            raise AssertionError('Api doesn\'t return operation id for this api call!')

        LOG.info('Wait up to 1 hour before image will be created')
        rebundle_result = wait_until(check_rebundle_api_finished, args=(server, operation_id), timeout=3600, logger=LOG)
        LOG.info('Rebundle is finished, api return: %s' % rebundle_result)
        setattr(world, 'api_image_id', rebundle_result['image_id'])
    else:
        LOG.info('Prepare server for image creation')
        prepare = server.api.image.prepare()
        LOG.debug('Prepare operation result: %s' % prepare)
        if CONF.feature.driver.current_cloud in (Platform.IDCF, Platform.CLOUDSTACK):
            node = world.cloud.get_node(server)
            volume = filter(lambda x: x.extra['instance_id'] == node.id, world.cloud.list_volumes())
            snapshot = world.cloud._driver._conn.create_volume_snapshot(volume[0])
            # 99 because this is Other Linux 64-bit in default cloudstack
            image_id = world.cloud._driver._conn.ex_create_snapshot_template(snapshot,
                                                        'tmp-revizor-%s' % datetime.now().strftime('%m%d%H%M'), 99).id
        else:
            image_id = world.cloud.create_template(world.cloud.get_node(server), name).id
        LOG.info('New image_id: %s' % image_id)
        setattr(world, 'api_image_id', image_id)

        LOG.info('Finalize server after rebundle')
        server.api.image.finalize()


def check_rebundle_api_finished(server, operation_id):
    resp = server.api.operation.result(operation_id=operation_id)
    LOG.debug('Server operation result: %s' % resp)
    if resp['error']:
        raise AssertionError('API operation result return error! Full api response:\n%s' % (resp))

    if resp['status'] == 'in-progress':
        return False
    elif resp['status'] == 'completed':
        return resp['result']

    return False


@step('I have a new image id')
def verify_have_image_id(step):
    image_id = getattr(world, 'api_image_id', None)
    assert image_id, 'Image id created via scalarizr api is empty'


@step('I create new role with this image id as ([\w\d]+)') #TODO: Rename this
def create_new_role(step, role_as):
    role_name = getattr(world, 'last_bundle_role_name')
    behaviors = CONF.feature.behaviors
    image_id = getattr(world, 'api_image_id', None)
    LOG.info('Create new Image in Scalr with image_id: "%s"' % image_id)
    image_details = IMPL.image.check(
        platform=CONF.feature.driver.scalr_cloud,
        cloud_location=CONF.platforms[CONF.feature.platform]['location'],
        image_id=image_id
    )

    IMPL.image.create(
        platform=CONF.feature.driver.scalr_cloud,
        cloud_location=CONF.platforms[CONF.feature.platform]['location'],
        image_id=image_id,
        name=image_details['name'],
        software=behaviors,
    )

    cloud_location = CONF.platforms[CONF.feature.platform]['location']
    if CONF.feature.driver.current_cloud == Platform.GCE:
        cloud_location = ""

    images = [{
        'platform': CONF.feature.driver.scalr_cloud,
        'cloudLocation': cloud_location,
        'imageId': image_id,
    }]

    LOG.info('Create new role %s with behaviors %s and image_id %s' % (role_name, behaviors, image_id))
    result = IMPL.role.create(name=role_name, behaviors=behaviors, images=images)
    LOG.info('New role id: %s' % result['role']['id'])
    setattr(world, '%s_id' % role_as, result['role']['id'])