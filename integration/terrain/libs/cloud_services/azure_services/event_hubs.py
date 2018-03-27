import time

import azure.mgmt.eventhub.models as az_models
from azure.mgmt.eventhub import EventHubManagementClient
import azure.common.exceptions as az_exceptions
from lettuce import world


class EventHubs(object):
    service_name = 'event hubs'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/Microsoft.EventHub']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = EventHubManagementClient(credentials=self.platform.get_credentials(),
                                          subscription_id=self.platform.subscription_id)
        ns_name, hub_name, group_name = self.platform.get_test_name('ns', 'hub', 'group')
        assert client.namespaces.check_name_availability(ns_name).name_available
        ns_params = az_models.EHNamespace(location='East US')
        client.namespaces.create_or_update(self.platform.resource_group_name, ns_name, ns_params)
        assert not client.namespaces.check_name_availability(ns_name).name_available

        for _ in range(0, 30):
            ns = client.namespaces.get(self.platform.resource_group_name, ns_name)
            if ns.provisioning_state == 'Succeeded':
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: namespace "%s" has not reached Succeeded '
                                 'state within 5 minutes' % ns_name)

        hub_params = az_models.Eventhub()
        client.event_hubs.create_or_update(self.platform.resource_group_name,
                                           ns_name,
                                           hub_name,
                                           hub_params)
        time.sleep(5)  # TODO: think of some context manager /w timeout for long-running operation
        hub = client.event_hubs.get(self.platform.resource_group_name, ns_name, hub_name)
        assert hub.status.value == 'Active'

        client.consumer_groups.create_or_update(self.platform.resource_group_name,
                                                ns_name,
                                                hub_name,
                                                group_name)
        time.sleep(5)
        client.consumer_groups.get(self.platform.resource_group_name,
                                   ns_name,
                                   hub_name,
                                   group_name)

        client.consumer_groups.delete(self.platform.resource_group_name, ns_name, hub_name,
                                      group_name)
        time.sleep(5)
        with world.assert_raises(az_models.ErrorResponseException, 'Not Found'):
            client.consumer_groups.get(self.platform.resource_group_name,
                                       ns_name,
                                       hub_name,
                                       group_name)

        client.event_hubs.delete(self.platform.resource_group_name, ns_name, hub_name)
        time.sleep(5)
        with world.assert_raises(az_models.ErrorResponseException, 'Not Found'):
            client.event_hubs.get(self.platform.resource_group_name, ns_name, hub_name)

        client.namespaces.delete(self.platform.resource_group_name, ns_name)

        for _ in range(0, 30):
            try:
                client.namespaces.get(self.platform.resource_group_name, ns_name)
            except az_models.ErrorResponseException as e:
                if 'Not Found' in str(e):
                    break
                else:
                    raise e
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: namespace "%s" has not been deleted '
                                 'within 5 minutes' % ns_name)

        assert client.namespaces.check_name_availability(ns_name).name_available

    def verify_denied(self, error_text):
        with world.assert_raises(az_exceptions.ClientException, error_text):
            client = EventHubManagementClient(credentials=self.platform.get_credentials(),
                                              subscription_id=self.platform.subscription_id)
            client.namespaces.check_name_availability('some_name')
