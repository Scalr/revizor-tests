import pytest

from revizor2 import CONF
from revizor2.api import Farm, IMPL
from revizor2.cloud import Cloud
from revizor2.consts import Dist, Platform
from revizor2.consts import ServerStatus
from revizor2.fixtures import resources

from scalarizr.lib import scalr as lib_scalr
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import node as lib_node
from scalarizr.lib import server as lib_server
from scalarizr.lib import apache as lib_apache
from scalarizr.integration.common import webhooks as lib_webhooks


class TestWebhooks:
    """
    Check fatmouse/workflow_engine webhooks implementation
    """

    order = (
        'test_prepare_testenv_without_ssl',
        'test_webhooks_without_ssl_verify',
        'test_scalr_mail_service',
        'test_webhooks_in_proxy',
        'test_prepare_testenv_with_ssl',
        'test_webhooks_with_ssl_verify')

    def test_prepare_testenv_without_ssl(self, testenv, ssl=False):
        params = {
            "scalr.system.webhooks.scalr_labs_workflow_engine": True,
            "scalr.system.webhooks.ssl_verify": ssl,
            "scalr.system.webhooks.retry_interval": 5,
            "scalr.system.webhooks.use_proxy": False}
        lib_scalr.update_scalr_config(testenv, params)
        testenv.restart_service("workflow-engine")
        testenv.restart_service("zmq_service")

    def test_webhooks_without_ssl_verify(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, testenv, webhooks=None, expected_results=None):
        server = servers.get('F1', None)
        if not server:
            lib_farm.add_role_to_farm(context, farm, dist='ubuntu1604')
            farm.launch()
            server = lib_server.wait_status(
                context, cloud, farm, status=ServerStatus.RUNNING)
            servers['F1'] = server
        node = cloud.get_node(server)
        node.put_file("/tmp/default",
                      resources('configs/nginx_to_flask_proxy.conf').get().decode("utf-8"))
        node.put_file("/tmp/prepare_flask.sh",
                      resources('scripts/prepare_flask.sh').get().decode("utf-8"))
        node.put_file('webhooks.py',
                      resources('scripts/webhooks.py').get().decode("utf-8"))  # Put flask script
        with node.remote_connection() as conn:
            # Run preparation script
            conn.run("sudo bash /tmp/prepare_flask.sh")
            # Run flask in background process
            conn.run("gunicorn -D -w 1 --bind localhost:5000 webhooks:app")
        lib_apache.assert_check_http_get_answer(server)
        webhooks = webhooks or [
            {'schema': 'http', 'endpoint': '/',  'trigger_event': 'AccountEvent', 'name': 'http_normal'},
            {'schema': 'http', 'endpoint': '/redirect', 'trigger_event': 'AccountEvent', 'name': 'http_redirect'},
            {'schema': 'http', 'endpoint': '/abort404', 'trigger_event': 'AccountEvent', 'name': 'http_404'},
            {'schema': 'http', 'endpoint': '/abort500', 'trigger_event': 'AccountEvent', 'name': 'http_500'},
            {'schema': 'http', 'endpoint': '/retry', 'trigger_event': 'AccountEvent', 'name': 'http_retry'},
            {'schema': 'https', 'endpoint': '/redirect', 'trigger_event': 'AccountEvent', 'name': 'https_redirect'},
            {'schema': 'https', 'endpoint': '/abort404', 'trigger_event': 'AccountEvent', 'name': 'https_404'},
            {'schema': 'https', 'endpoint': '/abort500', 'trigger_event': 'AccountEvent', 'name': 'https_500'},
            {'schema': 'https', 'endpoint': '/', 'trigger_event': 'AccountEvent', 'name': 'https_normal'},
        ]
        lib_webhooks.configure_webhooks(webhooks, server, farm, context)
        result = lib_node.execute_command(cloud, server, 'szradm --fire-event AccountEvent')
        assert not result.std_err, "Command szradm --fire-event AccountEvent failed with %s" % result.std_err
        expected_results = expected_results or [
            {'webhook_name': 'http_normal', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_redirect', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_404', 'expected_response': 404, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_500', 'expected_response': 500, 'attempts': 2, 'error': None},
            {'webhook_name': 'http_retry', 'expected_response': 200, 'attempts': 2, 'error': None},
            {'webhook_name': 'https_redirect', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'https_404', 'expected_response': 404, 'attempts': 1, 'error': None},
            {'webhook_name': 'https_500', 'expected_response': 500, 'attempts': 2, 'error': None},
            {'webhook_name': 'https_normal', 'expected_response': 200, 'attempts': 1, 'error': None},
        ]
        lib_webhooks.assert_webhooks(context['test_webhooks'], expected_results, server_id=server.id)
        assert not testenv.check_service_log("workflow-engine", "Traceback"), "Found Traceback in workflow-engine service log!"

    def test_scalr_mail_service(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, testenv):
        server = servers['F1']
        url = "http://%s.test-env.scalr.com/webhook_mail.php" % testenv.te_id
        params = {"scalr.system.webhooks.scalr_mail_service_url": url}
        lib_scalr.update_scalr_config(testenv, params)
        endpoints = IMPL.webhooks.list_endpoints()
        if endpoints and any(e for e in endpoints if e['url'] == 'SCALR_MAIL_SERVICE'):  # SCALR_MAIL_SERVICE endpoint already exists.
            endpoint = [e for e in endpoints if e['url'] == 'SCALR_MAIL_SERVICE'][0]
        else:  # Create new endpoint and change its url to "SCALR_MAIL_SERVICE" in database
            endpoint_name = "http://mail.test"
            endpoint = IMPL.webhooks.create_endpoint(endpoint_name, endpoint_name)
            endpoint['id'] = endpoint['endpointId']
            cmd = """mysql --database="scalr" --execute 'update webhook_endpoints set url="SCALR_MAIL_SERVICE" where url="http://mail.test"'"""
            testenv.get_ssh().run(cmd)  # Change url to SCALR_MAIL_SERVICE
        webhook_name = "test_mail_service"
        trigger_event = 'ScalrEvent'
        webhook = IMPL.webhooks.create_webhook(
            webhook_name,
            endpoint['id'],
            trigger_event,
            farm.id,
            attempts=2,
            user_data='test@scalr.com')
        lib_webhooks.update_saved_endpoints_and_hooks([endpoint], [webhook], context)
        testenv.restart_service("workflow-engine")
        result = lib_node.execute_command(cloud, server, 'szradm --fire-event %s' % trigger_event)
        assert not result.std_err, "Command szradm --fire-event %s failed with %s" % (trigger_event, result.std_err)
        result = lib_webhooks.wait_webhook_result(webhook)
        assert result['responseCode'] == 200, "SCALR_MAIL_SERVICE has unexpected exit code %s" % result['responseCode']
        assert not testenv.check_service_log("workflow-engine", "Traceback"), "Found Traceback in workflow-engine service log!"

    def test_webhooks_in_proxy(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, testenv):
        server = servers['F1']
        lib_farm.add_role_to_farm(context, farm, dist='ubuntu1404')
        farm.launch()
        proxy_server = lib_server.wait_status(
            context, cloud, farm, status=ServerStatus.RUNNING)
        servers['P1'] = proxy_server
        lib_server.execute_script(context, farm, proxy_server,
                                  script_name='https://git.io/vA52O',
                                  is_local=True,
                                  synchronous=True)       
        lib_scalr.configure_scalr_proxy(testenv, proxy_server, 'system.webhooks')
        testenv.restart_service("workflow-engine")
        testenv.restart_service("zmq_service")
        webhooks = [
            {'schema': 'http', 'endpoint': '/',  'trigger_event': 'AccountEvent', 'name': 'http_normal'},
            {'schema': 'https', 'endpoint': '/', 'trigger_event': 'AccountEvent', 'name': 'https_normal'}
        ]
        lib_webhooks.configure_webhooks(webhooks, server, farm, context)
        result = lib_node.execute_command(cloud, server, 'szradm --fire-event AccountEvent')
        assert not result.std_err, "Command szradm --fire-event AccountEvent failed with %s" % result.std_err
        expected_results = [
            {'webhook_name': 'http_normal', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'https_normal', 'expected_response': 200, 'attempts': 1, 'error': None}
        ]
        lib_webhooks.assert_webhooks(context['test_webhooks'], expected_results, server_id=server.id)
        assert not testenv.check_service_log("workflow-engine", "Traceback"), "Found Traceback in workflow-engine service log!"

    def test_prepare_testenv_with_ssl(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, testenv):
        self.test_prepare_testenv_without_ssl(testenv=testenv, ssl=True)

    def test_webhooks_with_ssl_verify(self, context: dict, cloud: Cloud, farm: Farm, servers: dict, testenv):
        webhooks = [
            {'schema': 'http', 'endpoint': '/', 'trigger_event': 'AccountEvent', 'name': 'http_normal'},
            {'schema': 'http', 'endpoint': '/redirect', 'trigger_event': 'AccountEvent', 'name': 'http_redirect'},
            {'schema': 'http', 'endpoint': '/abort404', 'trigger_event': 'AccountEvent', 'name': 'http_404'},
            {'schema': 'http', 'endpoint': '/abort500', 'trigger_event': 'AccountEvent', 'name': 'http_500'},
            {'schema': 'http', 'endpoint': '/retry', 'trigger_event': 'AccountEvent', 'name': 'http_retry'},
            {'schema': 'https', 'endpoint': '/', 'trigger_event': 'AccountEvent', 'name': 'https_normal'},
        ]
        expected_results = [
            {'webhook_name': 'http_normal', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_redirect', 'expected_response': 200, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_404', 'expected_response': 404, 'attempts': 1, 'error': None},
            {'webhook_name': 'http_500', 'expected_response': 500, 'attempts': 2, 'error': None},
            {'webhook_name': 'http_retry', 'expected_response': 200, 'attempts': 2, 'error': None},
            {'webhook_name': 'https_normal', 'expected_response': None, 'attempts': 2, 'error': 'certificate verify failed'},
        ]
        self.test_webhooks_without_ssl_verify(context=context, cloud=cloud, farm=farm, servers=servers, testenv=testenv, webhooks=webhooks, expected_results=expected_results)
