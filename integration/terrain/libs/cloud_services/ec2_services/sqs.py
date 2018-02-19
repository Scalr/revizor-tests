from botocore import exceptions as boto_exceptions
from lettuce import world


class Sqs(object):
    service_name = 'sqs'
    log_records = ['CONNECT queue.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('sqs')
        queue_name = self.platform.get_test_name()
        queue_url = client.create_queue(QueueName=queue_name)['QueueUrl']
        assert any([queue for queue in client.list_queues()['QueueUrls'] if queue == queue_url])
        assert client.get_queue_url(QueueName=queue_name)['QueueUrl'] == queue_url
        client.delete_queue(QueueUrl=queue_url)
        with world.assert_raises(boto_exceptions.ClientError, 'NonExistentQueue'):
            client.get_queue_url(QueueName=queue_name)
