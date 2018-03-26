import time

from botocore import exceptions as boto_exceptions
from lettuce import world

ATTRIBUTE_DEFINITIONS = [
    {
        'AttributeName': 'attr1',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'attr2',
        'AttributeType': 'S'
    }
]
KEY_SCHEMA = [
    {
        'AttributeName': 'attr1',
        'KeyType': 'HASH'
    },
    {
        'AttributeName': 'attr2',
        'KeyType': 'RANGE'
    }
]
PROVISIONED_THROUGHPUT = {
    'ReadCapacityUnits': 5,
    'WriteCapacityUnits': 5
}


class DynamoDb(object):
    service_name = 'dynamodb'
    log_records = ['https://dynamodb.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('dynamodb')
        table_name = self.platform.get_test_name()
        client.create_table(TableName=table_name,
                            AttributeDefinitions=ATTRIBUTE_DEFINITIONS,
                            KeySchema=KEY_SCHEMA,
                            ProvisionedThroughput=PROVISIONED_THROUGHPUT)
        assert any([table for table in client.list_tables()['TableNames'] if table == table_name])
        for _ in range(30):
            table = client.describe_table(TableName=table_name)['Table']
            if table['TableStatus'] == 'ACTIVE':
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: table "%s" has not been created '
                                 'within 5 minutes' % table_name)
        client.delete_table(TableName=table_name)
        for _ in range(30):
            if not any([table for table in client.list_tables()['TableNames'] if table == table_name]):
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: table "%s" has not been deleted '
                                 'within 5 minutes' % table_name)
        with world.assert_raises(boto_exceptions.ClientError, 'ResourceNotFoundException'):
            client.describe_table(TableName=table_name)

    def verify_denied(self, error_text):
        client = self.platform.get_client('dynamodb')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_tables()

    def verify_policy(self, prefix=False, pattern=False):
        client = self.platform.get_client('dynamodb')
        if prefix:
            table_name = self.platform.get_test_name('table_')
            with world.assert_raises(boto_exceptions.ClientError,
                                     "Action 'CreateTable' violates policy 'csg.resource.name.prefix'"):
                client.create_table(TableName=table_name,
                                    AttributeDefinitions=ATTRIBUTE_DEFINITIONS,
                                    KeySchema=KEY_SCHEMA,
                                    ProvisionedThroughput=PROVISIONED_THROUGHPUT)
        if pattern:
            table_name = 'tmp_%s' % self.platform.get_test_name()
            with world.assert_raises(boto_exceptions.ClientError,
                                     "Action 'CreateTable' violates policy 'csg.resource.name.validation_pattern'"):
                client.create_table(TableName=table_name,
                                    AttributeDefinitions=ATTRIBUTE_DEFINITIONS,
                                    KeySchema=KEY_SCHEMA,
                                    ProvisionedThroughput=PROVISIONED_THROUGHPUT)
        table_name = 'tmp_%s' % self.platform.get_test_name('table_')
        client.create_table(TableName=table_name,
                            AttributeDefinitions=ATTRIBUTE_DEFINITIONS,
                            KeySchema=KEY_SCHEMA,
                            ProvisionedThroughput=PROVISIONED_THROUGHPUT)
        for _ in range(30):
            table = client.describe_table(TableName=table_name)['Table']
            if table['TableStatus'] == 'ACTIVE':
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: table "%s" has not been created '
                                 'within 5 minutes' % table_name)
        client.delete_table(TableName=table_name)
        for _ in range(30):
            if not any([table for table in client.list_tables()['TableNames'] if table == table_name]):
                break
            time.sleep(10)
        else:
            raise AssertionError('Operation timed out: table "%s" has not been deleted '
                                 'within 5 minutes' % table_name)
