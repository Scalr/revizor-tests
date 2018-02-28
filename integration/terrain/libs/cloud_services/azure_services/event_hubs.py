import time

import azure.mgmt.eventhub.models as az_models
from azure.mgmt.eventhub import EventHubManagementClient
from lettuce import world


class EventHubs(object):
    service_name = 'event hubs'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = EventHubManagementClient(credentials=self.platform.credentials,
                                          subscription_id=self.platform.subscription_id)
        assert client.namespaces.check_name_availability('revizoreventhubstest').name_available
        ns_params = az_models.EHNamespace(location='East US')
        client.namespaces.create_or_update(self.platform.resource_group_name, 'revizoreventhubstest', ns_params)
        assert not client.namespaces.check_name_availability('revizoreventhubstest').name_available

        for _ in range(0, 30):
            ns = client.namespaces.get(self.platform.resource_group_name, 'revizoreventhubstest')
            if ns.provisioning_state == 'Succeeded':
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: namespace "revizoreventhubstest" has not reached Succeeded '
                                 'state within 5 minutes')

        hub_params = az_models.Eventhub()
        client.event_hubs.create_or_update(self.platform.resource_group_name,
                                           'revizoreventhubstest',
                                           'testhub',
                                           hub_params)
        time.sleep(5)  # TODO: think of some context manager /w timeout for long-running operation
        hub = client.event_hubs.get(self.platform.resource_group_name, 'revizoreventhubstest', 'testhub')
        assert hub.status.value == 'Active'

        client.consumer_groups.create_or_update(self.platform.resource_group_name,
                                                'revizoreventhubstest',
                                                'testhub',
                                                'testgroup')
        time.sleep(5)
        client.consumer_groups.get(self.platform.resource_group_name,
                                   'revizoreventhubstest',
                                   'testhub',
                                   'testgroup')

        client.consumer_groups.delete(self.platform.resource_group_name, 'revizoreventhubstest', 'testhub',
                                      'testgroup')
        time.sleep(5)
        with world.assert_raises(az_models.ErrorResponseException, 'Not Found'):
            client.consumer_groups.get(self.platform.resource_group_name,
                                       'revizoreventhubstest',
                                       'testhub',
                                       'testgroup')

        client.event_hubs.delete(self.platform.resource_group_name, 'revizoreventhubstest', 'testhub')
        time.sleep(5)
        with world.assert_raises(az_models.ErrorResponseException, 'Not Found'):
            client.event_hubs.get(self.platform.resource_group_name, 'revizoreventhubstest', 'testhub')

        client.namespaces.delete(self.platform.resource_group_name, 'revizoreventhubstest')

        for _ in range(0, 30):
            try:
                client.namespaces.get(self.platform.resource_group_name, 'revizoreventhubstest')
            except az_models.ErrorResponseException as e:
                if 'Not Found' in str(e):
                    break
                else:
                    raise e
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: namespace "revizoreventhubstest" has not been deleted '
                                 'within 5 minutes')

        assert client.namespaces.check_name_availability('revizoreventhubstest').name_available
