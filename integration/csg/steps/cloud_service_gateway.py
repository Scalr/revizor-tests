import logging

from lettuce import world, step
from revizor2.backend import IMPL


LOG = logging.getLogger(__name__)


@step('I have requested access to services on (AWS|Azure) as ([\w\d]+)')
def request_access(step, cloud, request_as):
    cloud = cloud.lower()
    services = []
    for item in step.hashes:
        services.append(item['service'].lower())
    id = IMPL.csg.create_request(cloud, services)
    if not id:
        raise AssertionError('Cloud service access request has not been created')
    LOG.debug('Created cloud service access request, id=%s' % id)
    setattr(world, '%s_request_id' % request_as, id)
    setattr(world, '%s_request_cloud' % request_as, cloud)


@step('I see access request ([\w\d]+) in ([\w\d]+) status on (environment|account) scope')
def verify_request_status(step, request_as, status, scope):
    id = getattr(world, '%s_request_id' % request_as)
    request = IMPL.csg.get_request(id, scope)
    if request['status'].lower() != status.lower():
        raise AssertionError('Cloud service access request status is incorrect. '
                             'Expected = "%s", actual = "%s"' % (status, request['status']))


@step('I approve access request ([\w\d]+)')
def approve_request(step, request_as):
    id = getattr(world, '%s_request_id' % request_as)
    cloud = getattr(world, '%s_request_cloud' % request_as)
    result = IMPL.csg.approve_request(id, cloud)
    if not result:
        raise AssertionError('Cloud service access request has not been approved')
    LOG.debug('Approved cloud service access request, id=%s' % id)


@step('I obtain secret key for access request ([\w\d]+)')
def obtain_key(step, request_as):
    id = getattr(world, '%s_request_id' % request_as)
    secret = IMPL.csg.get_secret(id)
    if not secret:
        raise AssertionError('Error getting secret key for cloud service access request, id=%s' % id)
    LOG.debug('Obtained secret key for cloud service access request, id=%s' % id)
    setattr(world, '%s_request_secret' % request_as, secret)
