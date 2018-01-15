from azure.mgmt.web import WebSiteManagementClient
import azure.mgmt.web.models as az_models

from base_azure import AzureCloudService


@AzureCloudService.register('web')
class Web(AzureCloudService):
    def _verify_impl(self):
        client = WebSiteManagementClient(credentials=self.credentials, subscription_id=self.subscription_id)
        assert client.check_name_availability('revizor-test-app', 'Site').name_available
        site = az_models.Site(location='Central US')
        client.web_apps.create_or_update(AzureCloudService.resource_group_name, 'revizor-test-app', site)
        assert not client.check_name_availability('revizor-test-app', 'Site').name_available
        app = client.web_apps.get(AzureCloudService.resource_group_name, 'revizor-test-app')
        assert app.state == 'Running'
        client.web_apps.delete(AzureCloudService.resource_group_name, 'revizor-test-app')
        assert client.check_name_availability('revizor-test-app', 'Site').name_available
