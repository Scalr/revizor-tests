from botocore import exceptions as boto_exceptions
from lettuce import world


class Ses(object):
    service_name = 'ses'
    log_records = ['https://email.us-east-1.amazonaws.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('ses')
        conf_name = self.platform.get_test_name()
        client.create_configuration_set(
            ConfigurationSet={
                'Name': conf_name
            }
        )
        assert any([conf for conf in client.list_configuration_sets()['ConfigurationSets']
                    if conf['Name'] == conf_name])
        client.delete_configuration_set(ConfigurationSetName=conf_name)
        with world.assert_raises(boto_exceptions.ClientError, 'ConfigurationSetDoesNotExist'):
            client.describe_configuration_set(ConfigurationSetName=conf_name)

    def verify_denied(self, error_text):
        client = self.platform.get_client('ses')
        with world.assert_raises(boto_exceptions.ClientError, error_text):
            client.list_configuration_sets()

    def verify_policy(self, prefix=False, pattern=False):
        client = self.platform.get_client('ses')
        if prefix:
            conf_name = self.platform.get_test_name('set_')
            with world.assert_raises(boto_exceptions.ClientError,
                                     "Action 'CreateConfigurationSet' violates policy 'csg.resource.name.prefix'"):
                client.create_configuration_set(
                    ConfigurationSet={
                        'Name': conf_name
                    }
                )
        if pattern:
            conf_name = 'tmp_%s' % self.platform.get_test_name()
            with world.assert_raises(boto_exceptions.ClientError,
                                     "Action 'CreateConfigurationSet' violates policy 'csg.resource.name.validation_pattern'"):
                client.create_configuration_set(
                    ConfigurationSet={
                        'Name': conf_name
                    }
                )
        conf_name = 'tmp_%s' % self.platform.get_test_name('set_')
        client.create_configuration_set(
            ConfigurationSet={
                'Name': conf_name
            }
        )
        assert any([conf for conf in client.list_configuration_sets()['ConfigurationSets']
                    if conf['Name'] == conf_name])
        client.delete_configuration_set(ConfigurationSetName=conf_name)
