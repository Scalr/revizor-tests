import time

from botocore import exceptions as boto_exceptions
from lettuce import world


class DynamoDb(object):
    service_name = 'dynamodb'
    log_records = ['https://dynamodb.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('dynamodb')
        table_name = self.platform.get_test_name()
        client.create_table(TableName=table_name,
                            AttributeDefinitions=[
                                {
                                    'AttributeName': 'attr1',
                                    'AttributeType': 'S'
                                },
                                {
                                    'AttributeName': 'attr2',
                                    'AttributeType': 'S'
                                }
                            ],
                            KeySchema=[
                                {
                                    'AttributeName': 'attr1',
                                    'KeyType': 'HASH'
                                },
                                {
                                    'AttributeName': 'attr2',
                                    'KeyType': 'RANGE'
                                }
                            ],
                            ProvisionedThroughput={
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            })
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
