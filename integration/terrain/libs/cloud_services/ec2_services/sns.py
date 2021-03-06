from botocore import exceptions as boto_exceptions
from lettuce import world


class Sns(object):
    service_name = 'sns'
    log_records = ['https://sns.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('sns')
        topic_name = self.platform.get_test_name()
        topic_arn = client.create_topic(Name=topic_name)['TopicArn']
        assert any([topic for topic in client.list_topics()['Topics'] if topic['TopicArn'] == topic_arn])
        client.delete_topic(TopicArn=topic_arn)
        with world.assert_raises(boto_exceptions.ClientError, 'NotFound'):
            client.get_topic_attributes(TopicArn=topic_arn)

    def verify_denied(self, error_text):
        client = self.platform.get_client('sns')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_topics()
