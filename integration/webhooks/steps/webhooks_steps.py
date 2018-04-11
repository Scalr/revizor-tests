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
    if tls:
        node.put_file("/tmp/default", resources('configs/nginx_to_flask_proxy_tls.conf').get())
    else:
        node.put_file("/tmp/default", resources('configs/nginx_to_flask_proxy.conf').get())  # Put custom nginx config in server
    node.put_file("/tmp/prepare_flask.sh", resources('scripts/prepare_flask.sh').get()) # Put flask preparation script in server
    node.put_file('webhooks.py', resources('scripts/webhooks.py').get())  # Put flask script
    with node.remote_connection() as conn:
        conn.run("sudo bash /tmp/prepare_flask.sh")  # Run preparation script
        conn.run("gunicorn -D -w 1 webhooks.py:app")  # Run flask in background process


@step(r'I add ([\w\d]+) webhooks to Scalr')
def configure_webhooks(step, serv_as):
    server = getattr(world, serv_as)
    created_webhooks = []
    created_endpoints = []
    current_endpoints = IMPL.webhooks.list_endpoints()
    for opts in step.hashes:
        url = "%s://%s%s" % (opts['schema'].strip(), server.public_ip, opts['endpoint'].strip())
        if current_endpoints and any(e for e in current_endpoints.values() if e['url'] == url):
            continue
        scalr_endpoint = IMPL.webhooks.create_endpoint(url)
        created_endpoints.append(scalr_endpoint)
        webhook = IMPL.webhooks.create_webhook(
            opts['name'].strip() + '-' + server.id.split('-')[0],
            [scalr_endpoint['endpointId']],
            [opts['trigger_event'].strip()],
            [world.farm.id],
            attempts=2)
        created_webhooks.append(webhook)
    setattr(world, 'test_endpoints', created_endpoints)
    setattr(world, 'test_webhooks', created_webhooks)


@step(r'I assert ([\w\d]+) webhook results')
def assert_webhooks(step, serv_as):
    server = getattr(world, serv_as)
    webhooks = getattr(world, 'test_webhooks')
    for opts in step.hashes:
        webhook_name = opts['webhook_name'] + '-' + server.id.split('-')[0]
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


@step(r'I configure SCALR_MAIL_SERVICE')
def configure_scalr_mail_service(step):
    url = "http://%s.test-env.scalr.com/webhook_mail.php" % world.testenv.te_id
    step.behave_as("""
        And I have configured scalr config:
            | name                                          | value |
            | scalr.system.webhooks.scalr_mail_service_url  | {url} |""".format(url=url))
    if not any(hook for hook in IMPL.webhooks.list_webhooks() if hook['name'] == 'test_mail_service'):
        endpoints = IMPL.webhooks.list_endpoints()
        if endpoints:
            endpoint = [endp for endp in endpoints.values() if endp['url'] == 'http://mail.test']
            endpoint = endpoint[0] if endpoint else IMPL.webhooks.create_endpoint("http://mail.test")
        else:
            endpoint = IMPL.webhooks.create_endpoint("http://mail.test")
        cmd = """mysql --database="scalr" --execute 'update webhook_endpoints set url="SCALR_MAIL_SERVICE" where url="http://mail.test"'"""
        world.testenv.get_ssh().run(cmd)  # Change url to SCALR_MAIL_SERVICE
        webhook = IMPL.webhooks.create_webhook(
            "test_mail_service",
            [endpoint['endpointId']],
            'ScalrEvent',
            [world.farm.id],
            attempts=2,
            user_data='test@scalr.com')
        setattr(world, 'mail_endpoint', endpoint)
        setattr(world, 'mail_webhook', webhook)


@step(r'SCALR_MAIL_SERVICE result is successful')
def assert_mail_service(step):
    webhook = getattr(world, 'mail_webhook')
    endpoint = getattr(world, 'mail_endpoint', None)
    result = wait_webhook_result(webhook)
    assert result['responseCode'] == 200, "SCALR_MAIL_SERVICE has unexpected exit code %s" % result['responseCode']
    IMPL.webhooks.delete_webhooks([webhook['webhookId']])
    IMPL.webhooks.delete_endpoints([endpoint['endpointId']])


def wait_webhook_result(webhook, attempts=None, expect_to_fail=False):
    for i in range(20):
        result = IMPL.webhooks.get_webhook_results(webhook_ids=[webhook['webhookId']])
        if result:
            LOG.debug('Webhook %s current history:\n%s' % (webhook['name'], result[0]))
            if attempts and result[0]['handleAttempts'] != attempts:
                time.sleep(10)
                continue
            elif result[0]['responseCode'] or expect_to_fail:
                return result[0]
        time.sleep(10)
    raise AssertionError('Cant find results for webhook %s.' % webhook['name'])
