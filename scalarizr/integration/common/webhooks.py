import logging
import time

from revizor2.backend import IMPL
from revizor2.api import Server, Farm


LOG = logging.getLogger(__name__)


def configure_webhooks(webhooks: list, server: Server, farm: Farm, context: dict):
    created_webhooks = []
    created_endpoints = []
    current_endpoints = IMPL.webhooks.list_endpoints()
    LOG.debug('Current endpoints:%s' % current_endpoints)
    current_endpoint_urls = [e['url'] for e in current_endpoints] if current_endpoints else []
    for opts in webhooks:
        url = "%s://%s%s" % (opts['schema'].strip(),
                             server.public_ip, opts['endpoint'].strip())
        if url in current_endpoint_urls:
            continue
        name = opts['name'].strip()
        scalr_endpoint = IMPL.webhooks.create_endpoint(name, url)
        created_endpoints.append(scalr_endpoint)
        webhook = IMPL.webhooks.create_webhook(
            '%s-%s' % (opts['name'].strip(), server.id.split('-')[0]),
            scalr_endpoint['endpointId'],
            opts['trigger_event'].strip(),
            farm.id,
            attempts=2)
        created_webhooks.append(webhook)
    LOG.debug('Created test endpoints: %s' % created_endpoints)
    LOG.debug('Created test webhooks: %s' % created_webhooks)
    update_saved_endpoints_and_hooks(
        created_endpoints, created_webhooks, context)


def wait_webhook_result(webhook: dict, attempts: int=None, expect_to_fail: bool=False):
    for _ in range(20):
        result = IMPL.webhooks.get_webhook_results(
            webhook_ids=webhook['webhookId'])
        if result:
            LOG.debug('Webhook %s current history:\n%s' %
                      (webhook['name'], result[0]))
            if attempts and result[0]['handleAttempts'] != attempts:
                time.sleep(10)
                continue
            elif result[0]['responseCode'] or expect_to_fail:
                return result[0]
        time.sleep(10)
    raise AssertionError('Cant find results for webhook %s.' % webhook['name'])


def assert_webhooks(webhooks: list, expected_results: list, server_id: str=None):
    for opts in expected_results:
        if server_id:
            webhook_name = '%s-%s' % (opts['webhook_name'],
                                      server_id.split('-')[0])
        else:
            webhook_name = opts['webhook_name']
        webhook = [w for w in webhooks if w['name'] == webhook_name][0]
        LOG.debug('Check webhook %s' % webhook['name'])
        fail = False if opts.get('expected_response') else True
        result = wait_webhook_result(
            webhook, attempts=opts['attempts'], expect_to_fail=fail)
        LOG.debug("Found result for webhook %s.\n%s" %
                  (webhook['name'], result))
        if fail:
            assert opts['error'].strip() in result['errorMsg'],\
                "Wrong error message and/or ResponceCode for webhook %s! Message - %s, code - %s" % (
                    opts['webhook_name'],
                    result['errorMsg'],
                    result['responceCode'])
        else:
            assert result['responseCode'] == opts['expected_response'],\
                "Wrong response code for webhook %s! Expected - %s, actual - %s" % (
                    opts['webhook_name'],
                    opts['expected_response'],
                    result['responseCode'])
        if opts['attempts']:
            assert result['handleAttempts'] == opts['attempts'],\
                "Wrong number of attempts for webhook %s! Expected %s, actual %s" % (
                    opts['webhook_name'],
                    opts['attempts'],
                    result['handleAttempts'])


def update_saved_endpoints_and_hooks(endpoints: list, webhooks: list, context: dict):
    updated_endpoints = context.get('test_endpoints', []) + endpoints
    updated_webhooks = context.get('test_webhooks', []) + webhooks
    context['test_endpoints'] = updated_endpoints
    LOG.debug('Updated endpoints in world:%s' % updated_endpoints)
    context['test_webhooks'] = updated_webhooks
    LOG.debug("Updated webhooks in world:%s" % updated_webhooks)
