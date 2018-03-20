from azure.mgmt.monitor import MonitorManagementClient
import azure.mgmt.monitor.models as az_models
import azure.common.exceptions as az_exceptions
from lettuce import world


class Insights(object):
    service_name = 'insights'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/microsoft.insights']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = MonitorManagementClient(credentials=self.platform.get_credentials(),
                                         subscription_id=self.platform.subscription_id)
        action_group_name = self.platform.get_test_name()
        action_group = az_models.ActionGroupResource(location='global', group_short_name=action_group_name[:12])
        client.action_groups.create_or_update(resource_group_name=self.platform.resource_group_name,
                                              action_group_name=action_group_name,
                                              action_group=action_group)
        assert any([group for group
                    in list(client.action_groups.list_by_resource_group(
                            resource_group_name=self.platform.resource_group_name))
                    if group.name == action_group_name])
        assert client.action_groups.get(resource_group_name=self.platform.resource_group_name,
                                        action_group_name=action_group_name).group_short_name == action_group_name[:12]
        client.action_groups.delete(resource_group_name=self.platform.resource_group_name,
                                    action_group_name=action_group_name)
        assert client.action_groups.get(resource_group_name=self.platform.resource_group_name,
                                        action_group_name=action_group_name) is None

    def verify_denied(self, error_text):
        with world.assert_raises(az_exceptions.ClientException, error_text):
            client = MonitorManagementClient(credentials=self.platform.get_credentials(),
                                             subscription_id=self.platform.subscription_id)
            list(client.action_groups.list_by_resource_group(resource_group_name=self.platform.resource_group_name))
