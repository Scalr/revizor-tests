from azure.mgmt.containerservice import ContainerServiceClient


class ContainerService(object):
    service_name = 'container service'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = ContainerServiceClient(credentials=self.platform.credentials,
                                        subscription_id=self.platform.subscription_id)
        services = client.container_services.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(services)) == 0
        clusters = client.managed_clusters.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(clusters)) == 0
