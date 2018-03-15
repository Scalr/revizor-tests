from azure.mgmt.web import WebSiteManagementClient
import azure.mgmt.web.models as az_models


class Web(object):
    service_name = 'web'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/Microsoft.Web']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = WebSiteManagementClient(credentials=self.platform.credentials,
                                         subscription_id=self.platform.subscription_id)
        app_name = self.platform.get_test_name()
        assert client.check_name_availability(app_name, 'Site').name_available
        site = az_models.Site(location='Central US')
        client.web_apps.create_or_update(self.platform.resource_group_name, app_name, site)
        try:
            assert not client.check_name_availability(app_name, 'Site').name_available
            app = client.web_apps.get(self.platform.resource_group_name, app_name)
            assert app.state == 'Running'
        finally:
            client.web_apps.delete(self.platform.resource_group_name, app_name)
        assert client.check_name_availability(app_name, 'Site').name_available
