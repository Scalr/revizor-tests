import logging

from lettuce import world, step

from revizor2.backend import IMPL
from revizor2.conf import CONF
from revizor2.helpers import cloud_services


LOG = logging.getLogger(__name__)


@step('I have requested access to services on (AWS|Azure) as ([\w\d]+):')
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


@step('I see access request ([\w\d]+) in ([\w\d]+) status(?: on (environment|account) scope)?')
def verify_request_status(step, request_as, status, scope):
    id = getattr(world, '%s_request_id' % request_as)
    if scope is None:
        scope = 'environment'
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


@step('I have ([\w\d]+) access request ([\w\d]+)')
def have_request(step, status, request_as):
    step.given("I see access request {request_as} in {status} status".format(
        request_as=request_as,
        status=status))


@step('I execute "([\w\d-]+)" for ([\w\d]+) service on (AWS|Azure) using ([\w\d]+)')
def execute_service_function(step, func, service, cloud, request_as):
    id = getattr(world, '%s_request_id' % request_as)
    secret = getattr(world, '%s_request_secret' % request_as)
    request = IMPL.csg.get_request(id)
    csg_port = world.get_scalr_config_value('scalr.csg.endpoint.port')
    result = None
    if cloud.lower() == 'aws':
        aws = cloud_services.Aws(id,
                                 request['access_key'],
                                 secret,
                                 'us-east-1',  # TODO: think how can we get it instead of hardcoding
                                 '%s.test-env.scalr.com' % CONF.scalr.te_id,
                                 csg_port)
        aws.configure()
        result = aws.execute_function(service.lower(), func.lower())
    setattr(world, 'csg_last_result', result)


@step('the response contains no errors')
def verify_response_no_error(step):
    result = getattr(world, 'csg_last_result')
    if result is None:
        raise AssertionError('No recent CSG response found')
    if result['status'] != 200 or result.get('error'):
        raise AssertionError('Service response is not valid. '
                             'HTTP status = %s, Error = "%s"' % (result['status'], result.get('error')))


@step('the response contains access error')
def verify_response_access_error(step):
    result = getattr(world, 'csg_last_result')
    if result is None:
        raise AssertionError('No recent CSG response found')
    if result['status'] not in [400, 401, 403] or not result.get('error'):
        raise AssertionError('Service response is not valid. '
                             'HTTP status = %s, Error = %s' % (result['status'], result.get('error')))


@step('I set proxy for ([\w\d,]+) in Scalr to ([\w\d]+)')
def configure_scalr_proxy(step, clouds, proxy_as):
    clouds = [c.strip().lower() for c in clouds.split(',')]
    server = getattr(world, proxy_as)
    params = [
        {'name': 'scalr.connections.proxy.host', 'value': server.public_ip},
        {'name': 'scalr.connections.proxy.port', 'value': 3128},
        {'name': 'scalr.connections.proxy.user', 'value': 'testuser'},
        {'name': 'scalr.connections.proxy.pass', 'value': 'p@ssw0rd'},
        {'name': 'scalr.connections.proxy.type', 'value': 0},
        {'name': 'scalr.connections.proxy.authtype', 'value': 1},
        {'name': 'scalr.connections.proxy.use_on', 'value': 'scalr'}
    ]
    for cloud in clouds:
        params.append(
            {'name': 'scalr.%s.use_proxy' % cloud, 'value': True}
        )
    world.update_scalr_config(params)


@step('last proxy logs on ([\w\d]+) contain "(.+)"')
def check_proxy_logs(step, proxy_as, contain):
    server = getattr(world, proxy_as)
    node = world.cloud.get_node(server)
    old_logs = getattr(world, '%s_proxy_logs' % proxy_as, [])
    logs = node.run('cat /var/log/squid3/access.log')[0].splitlines()
    setattr(world, '%s_proxy_logs' % proxy_as, logs)
    for line in logs:
        if contain in line and line not in old_logs:
            break
    else:
        LOG.debug('Received squid logs:\n%s' % logs)
        raise AssertionError('Text "%s" not found in last proxy logs' % contain)
