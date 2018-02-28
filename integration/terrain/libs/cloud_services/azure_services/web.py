from azure.mgmt.web import WebSiteManagementClient
import azure.mgmt.web.models as az_models


class Web(object):
    service_name = 'web'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = WebSiteManagementClient(credentials=self.platform.credentials,
                                         subscription_id=self.platform.subscription_id)
        assert client.check_name_availability('revizor-test-app', 'Site').name_available
        site = az_models.Site(location='Central US')
        client.web_apps.create_or_update(self.platform.resource_group_name, 'revizor-test-app', site)
        try:
            assert not client.check_name_availability('revizor-test-app', 'Site').name_available
            app = client.web_apps.get(self.platform.resource_group_name, 'revizor-test-app')
            assert app.state == 'Running'
        finally:
            client.web_apps.delete(self.platform.resource_group_name, 'revizor-test-app')
        assert client.check_name_availability('revizor-test-app', 'Site').name_available
