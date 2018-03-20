from azure.mgmt.containerservice import ContainerServiceClient
import azure.common.exceptions as az_exceptions
from lettuce import world


class ContainerService(object):
    service_name = 'container service'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/Microsoft.ContainerService']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = ContainerServiceClient(credentials=self.platform.get_credentials(),
                                        subscription_id=self.platform.subscription_id)
        services = client.container_services.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(services)) == 0
        clusters = client.managed_clusters.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(clusters)) == 0

    def verify_denied(self, error_text):
        with world.assert_raises(az_exceptions.ClientException, error_text):
            client = ContainerServiceClient(credentials=self.platform.get_credentials(),
                                            subscription_id=self.platform.subscription_id)
            list(client.container_services.list_by_resource_group(
                resource_group_name=self.platform.resource_group_name))
