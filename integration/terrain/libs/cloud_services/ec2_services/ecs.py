class Ecs(object):
    service_name = 'ecs'
    log_records = ['CONNECT ecs.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('ecs')
        client.list_clusters(maxResults=10)
        client.list_task_definition_families(maxResults=10)
        client.list_task_definitions(maxResults=10)