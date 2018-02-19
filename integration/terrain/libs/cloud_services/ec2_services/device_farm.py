from botocore import exceptions as boto_exceptions
from lettuce import world


class DeviceFarm(object):
    service_name = 'device farm'
    log_records = ['CONNECT devicefarm.us-west-2.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('devicefarm', region='us-west-2')
        project_name = self.platform.get_test_name()
        project_arn = client.create_project(name=project_name)['project']['arn']
        assert any([proj for proj in client.list_projects()['projects']
                    if proj['name'] == project_name])
        assert client.get_project(arn=project_arn)['project']['name'] == project_name
        client.delete_project(arn=project_arn)
        with world.assert_raises(boto_exceptions.ClientError, 'NotFound'):
            client.get_project(arn=project_arn)