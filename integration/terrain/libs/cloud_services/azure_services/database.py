import time

import azure.mgmt.sql.models as az_models
from azure.mgmt.sql import SqlManagementClient
import azure.common.exceptions as az_exceptions
from lettuce import world


class Database(object):
    service_name = 'database'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/Microsoft.Sql']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = SqlManagementClient(credentials=self.platform.get_credentials(),
                                     subscription_id=self.platform.subscription_id)
        server_name, database_name = self.platform.get_test_name('sqlserver', 'db')
        servers = list(client.servers.list_by_resource_group(resource_group_name=self.platform.resource_group_name))
        servers_count = len(servers)
        availability = client.servers.check_name_availability(server_name)
        assert availability.available
        parameters = az_models.Server(location='East US', administrator_login='revizor',
                                      administrator_login_password='qwert123!@#')
        client.servers.create_or_update(resource_group_name=self.platform.resource_group_name, server_name=server_name,
                                        parameters=parameters)
        for _ in range(30):
            servers = list(client.servers.list_by_resource_group(resource_group_name=self.platform.resource_group_name))
            if len(servers) > servers_count:
                servers_count = len(servers)
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: SQL server "%s" has not been created '
                                 'within 5 minutes' % server_name)

        availability = client.servers.check_name_availability(server_name)
        assert not availability.available
        server = client.servers.get(resource_group_name=self.platform.resource_group_name, server_name=server_name)
        assert server.state == 'Ready'

        dbs = list(client.databases.list_by_server(resource_group_name=self.platform.resource_group_name,
                                                   server_name=server_name))
        dbs_count = len(dbs)
        parameters = az_models.Database(location='East US')
        client.databases.create_or_update(resource_group_name=self.platform.resource_group_name,
                                          server_name=server_name,
                                          database_name=database_name, parameters=parameters)
        for _ in range(30):
            dbs = list(client.databases.list_by_server(resource_group_name=self.platform.resource_group_name,
                                                       server_name=server_name))
            if len(dbs) > dbs_count:
                dbs_count = len(dbs)
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: database "%s" has not been created '
                                 'within 5 minutes' % database_name)

        db = client.databases.get(resource_group_name=self.platform.resource_group_name, server_name=server_name,
                                  database_name=database_name)
        assert db.status == 'Online'

        client.databases.delete(resource_group_name=self.platform.resource_group_name, server_name=server_name,
                                database_name=database_name)
        for _ in range(30):
            dbs = list(client.databases.list_by_server(resource_group_name=self.platform.resource_group_name,
                                                       server_name=server_name))
            if len(dbs) < dbs_count:
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: database "%s" has not been deleted '
                                 'within 5 minutes' % database_name)

        with world.assert_raises(az_exceptions.CloudError, 'ResourceNotFound'):
            client.databases.get(resource_group_name=self.platform.resource_group_name, server_name=server_name,
                                 database_name=database_name)

        client.servers.delete(resource_group_name=self.platform.resource_group_name, server_name=server_name)
        for _ in range(30):
            servers = list(client.servers.list_by_resource_group(resource_group_name=self.platform.resource_group_name))
            if len(servers) < servers_count:
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: SQL server "%s" has not been deleted '
                                 'within 5 minutes' % server_name)

        with world.assert_raises(az_exceptions.CloudError, 'ResourceNotFound'):
            client.servers.get(resource_group_name=self.platform.resource_group_name, server_name=server_name)

    def verify_denied(self, error_text):
        with world.assert_raises(az_exceptions.ClientException, error_text):
            client = SqlManagementClient(credentials=self.platform.get_credentials(),
                                         subscription_id=self.platform.subscription_id)
            list(client.servers.list_by_resource_group(resource_group_name=self.platform.resource_group_name))
