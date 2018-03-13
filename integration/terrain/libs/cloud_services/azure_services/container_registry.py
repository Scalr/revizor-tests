from azure.mgmt.containerregistry import ContainerRegistryManagementClient
import azure.mgmt.containerregistry.models as az_models


class ContainerRegistry(object):
    service_name = 'container registry'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = ContainerRegistryManagementClient(credentials=self.platform.credentials,
                                                   subscription_id=self.platform.subscription_id)
        registry_name = self.platform.get_test_name()
        registries = client.registries.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        registries_count = len(list(registries))
        availability = client.registries.check_name_availability(registry_name)
        assert availability.name_available
        sku = az_models.Sku(name=az_models.SkuName.standard)
        registry = az_models.Registry(location='eastus', sku=sku)
        client.registries.create(resource_group_name=self.platform.resource_group_name,
                                 registry_name=registry_name,
                                 registry=registry)
        registries = client.registries.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(registries)) == registries_count + 1
        availability = client.registries.check_name_availability(registry_name)
        assert not availability.name_available
        new_registry = client.registries.get(resource_group_name=self.platform.resource_group_name,
                                             registry_name=registry_name)
        assert new_registry.provisioning_state == 'Succeeded'
        client.registries.delete(resource_group_name=self.platform.resource_group_name,
                                 registry_name=registry_name)
        registries = client.registries.list_by_resource_group(resource_group_name=self.platform.resource_group_name)
        assert len(list(registries)) == registries_count
        availability = client.registries.check_name_availability(registry_name)
        assert availability.name_available
