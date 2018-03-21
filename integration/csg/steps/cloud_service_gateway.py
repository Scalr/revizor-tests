import logging

from lettuce import world, step

from revizor2.backend import IMPL


LOG = logging.getLogger(__name__)


@step('I have requested access to services on (AWS|Azure) as ([\w\d]+):')
def request_access(step, cloud, request_as):
    cloud = cloud.lower()
    if cloud == 'aws':
        cloud = 'ec2'
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
def verify_request_status(step, request_as, status, scope='environment'):
    id = getattr(world, '%s_request_id' % request_as)
    request = IMPL.csg.get_request(id, scope)
    if request['status'].lower() != status.lower():
        raise AssertionError('Cloud service access request status is incorrect. '
                             'Expected = "%s", actual = "%s"' % (status, request['status']))


@step('I (approve|deny|revoke|archive) access request ([\w\d]+)')
def approve_request(step, action, request_as):
    id = getattr(world, '%s_request_id' % request_as)
    if action == 'approve':
        cloud = getattr(world, '%s_request_cloud' % request_as)
        result = IMPL.csg.approve_request(id, cloud)
        if not result:
            raise AssertionError('Cloud service access request has not been approved')
        LOG.debug('Approved cloud service access request, id=%s' % id)
    elif action == 'deny':
        IMPL.csg.deny_request(id)
    elif action == 'revoke':
        IMPL.csg.revoke_request(id)
    elif action == 'archive':
        IMPL.csg.archive_request(id)


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


@step("\"([\w\d\s]+)\" service is (active|restricted|disabled) on (AWS|Azure) using ([\w\d]+)")
def verify_service(step, service, status, platform, request_as):
    """`status` - defines in which state the service should be
      - active: service is approved and should work properly
      - restricted: access request is approved, but this service is not in a list of requested services
      - disabled: access request was approved once but then revoked or archived
    Both restricted/disabled states do mean that the service doesn't work, but the error expected differs for them
    """
    service = service.strip().lower()
    platform = platform.strip().lower()
    if platform == 'aws':
        platform = 'ec2'
    request_id = getattr(world, '%s_request_id' % request_as)
    secret = getattr(world, '%s_request_secret' % request_as)
    world.csg_verify_service(platform, service, request_id, secret, status)


@step("requests to \"([\w\d\s]+)\" on (AWS|Azure) are present in last proxy logs on ([\w\d]+)")
def check_proxy_logs(step_instance, service, platform, proxy_as):
    service = service.strip().lower()
    platform = platform.strip().lower()
    if platform == 'aws':
        platform = 'ec2'
    server = getattr(world, proxy_as)
    node = world.cloud.get_node(server)
    old_logs_count = getattr(world, '%s_proxy_logs_count' % proxy_as, 0)
    logs = node.run('tail -n +%s /var/log/mitmproxy.log' % (old_logs_count + 1)).std_out.splitlines()
    setattr(world, '%s_proxy_logs_count' % proxy_as, len(logs) + old_logs_count)
    for record in world.csg_get_service_log_records(platform, service):
        LOG.debug('Searching for "%s" in proxy logs' % record)
        for line in logs:
            if record in line:
                break
        else:
            # record not found in logs
            LOG.debug('Received proxy logs:\n%s' % logs)
            raise AssertionError('Text "%s" not found in last proxy logs' % record)
