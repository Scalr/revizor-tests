import logging
import time

from lettuce import world, step

from revizor2.fixtures import resources
from revizor2.backend import IMPL

LOG = logging.getLogger(__name__)


@step(r'I configure nginx/flask on ([\w\d]+)(?: with (TLSv1.2))?')
def configure_flask(step, serv_as, tls):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    node.put_file("/tmp/default", resources('configs/nginx_to_flask_proxy.conf').get())  # Put custom nginx config in server
    # if tls:
    #     node.run("ex -sc '13i|        ssl_protocols TLSv1.2;' -cx /tmp/default")
    node.put_file("/tmp/prepare_flask.sh", resources('scripts/prepare_flask.sh').get()) # Put flask preparation script in server
    node.put_file('webhooks.py', resources('scripts/webhooks.py').get())  # Put flask script
    with node.remote_connection() as conn:
        conn.run("sudo bash /tmp/prepare_flask.sh")  # Run preparation script
        conn.run("gunicorn -D -w 1 --bind localhost:5000 webhooks:app")  # Run flask in background process


@step(r'I add ([\w\d]+) webhooks to Scalr')
def configure_webhooks(step, serv_as):
    server = getattr(world, serv_as)
    created_webhooks = []
    created_endpoints = []
    current_endpoints = IMPL.webhooks.list_endpoints()
    LOG.debug('Current endpoints:%s' % current_endpoints)
    current_endpoint_urls = [e['url'] for e in current_endpoints] if current_endpoints else None
    for opts in step.hashes:
        url = "%s://%s%s" % (opts['schema'].strip(), server.public_ip, opts['endpoint'].strip())
        if current_endpoint_urls and url in current_endpoint_urls:
            continue
        name = opts['name'].strip()
        scalr_endpoint = IMPL.webhooks.create_endpoint(name, url)
        created_endpoints.append(scalr_endpoint)
        webhook = IMPL.webhooks.create_webhook(
            '%s-%s' % (opts['name'].strip(), server.id.split('-')[0]),
            scalr_endpoint['endpointId'],
            opts['trigger_event'].strip(),
            world.farm.id,
            attempts=2)
        created_webhooks.append(webhook)
    LOG.debug('Created test endpoints: %s' % created_endpoints)
    LOG.debug('Created test webhooks: %s' % created_webhooks)
    update_saved_endpoints_and_hooks(created_endpoints, created_webhooks)


@step(r'I assert ([\w\d]+) webhook results')
def assert_webhooks(step, serv_as):
    server = getattr(world, serv_as)
    webhooks = getattr(world, 'test_webhooks')
    LOG.debug("Found test webhooks: %s" % webhooks)
    for opts in step.hashes:
        webhook_name = '%s-%s' % (opts['webhook_name'], server.id.split('-')[0])
        webhook = [w for w in webhooks if w['name'] == webhook_name][0]
        LOG.debug('Check webhook %s' % webhook['name'])
        fail = True if opts['expected_response'] == "None" else False
        result = wait_webhook_result(webhook, attempts=int(opts['attempts']), expect_to_fail=fail)
        LOG.debug("Found result for webhook %s.\n%s" % (webhook['name'], result))
        if fail:
            assert opts['error'].strip() in result['errorMsg'],\
                "Wrong error message and/or ResponceCode for webhook %s! Message - %s, code - %s" % (
                    opts['webhook_name'],
                    result['errorMsg'],
                    result['responceCode'])
        else:
            assert result['responseCode'] == int(opts['expected_response']),\
                "Wrong response code for webhook %s! Expected - %s, actual - %s" % (
                    opts['webhook_name'],
                    opts['expected_response'],
                    result['responseCode'])
        assert result['handleAttempts'] == int(opts['attempts']),\
            "Wrong number of attempts for webhook %s! Expected %s, actual %s" % (
                opts['webhook_name'],
                opts['attempts'],
                result['handleAttempts'])


@step(r'I set scalr_mail_service_url in TestEnv config')
def set_mail_service_url(step):
    url = "http://%s.test-env.scalr.com/webhook_mail.php" % world.testenv.te_id
    step.behave_as("""
        And I have configured scalr config:
            | name                                          | value |
            | scalr.system.webhooks.scalr_mail_service_url  | {url} |""".format(url=url))


@step(r'I add SCALR_MAIL_SERVICE webhook')
def add_mail_service_webhook(step):
    endpoints = IMPL.webhooks.list_endpoints()
    if endpoints and any(e for e in endpoints if e['url'] == 'SCALR_MAIL_SERVICE'):
        endpoint = [endp for endp in endpoints if endp['url'] == 'SCALR_MAIL_SERVICE'][0]
    else:
        url = "http://mail.test"
        name = url
        endpoint = IMPL.webhooks.create_endpoint(name, url)
        endpoint['id'] = endpoint['endpointId']
        cmd = """mysql --database="scalr" --execute 'update webhook_endpoints set url="SCALR_MAIL_SERVICE" where url="http://mail.test"'"""
        world.testenv.get_ssh().run(cmd)  # Change url to SCALR_MAIL_SERVICE
    webhook = IMPL.webhooks.create_webhook(
        "test_mail_service",
        endpoint['id'],
        'ScalrEvent',
        world.farm.id,
        attempts=2,
        user_data='test@scalr.com')
    update_saved_endpoints_and_hooks([endpoint], [webhook])
    LOG.debug('Mail service endpoint %s.\nMail service webhook %s' % (endpoint, webhook))


@step(r'SCALR_MAIL_SERVICE result is successful')
def assert_mail_service(step):
    webhook = getattr(world, 'test_webhooks')[0]
    result = wait_webhook_result(webhook)
    assert result['responseCode'] == 200, "SCALR_MAIL_SERVICE has unexpected exit code %s" % result['responseCode']


def wait_webhook_result(webhook, attempts=None, expect_to_fail=False):
    for _ in range(20):
        result = IMPL.webhooks.get_webhook_results(webhook_ids=webhook['webhookId'])
        if result:
            LOG.debug('Webhook %s current history:\n%s' % (webhook['name'], result[0]))
            if attempts and result[0]['handleAttempts'] != attempts:
                time.sleep(10)
                continue
            elif result[0]['responseCode'] or expect_to_fail:
                return result[0]
        time.sleep(10)
    raise AssertionError('Cant find results for webhook %s.' % webhook['name'])


def update_saved_endpoints_and_hooks(endpoints, webhooks):
    updated_endpoints = getattr(world, 'test_endpoints', []) + endpoints
    updated_webhooks = getattr(world, 'test_webhooks', []) + webhooks
    setattr(world, 'test_endpoints', updated_endpoints)
    LOG.debug('Updated endpoints in world:%s' % updated_endpoints)
    setattr(world, 'test_webhooks', updated_webhooks)
    LOG.debug("Updated webhooks in world:%s" % updated_webhooks)
