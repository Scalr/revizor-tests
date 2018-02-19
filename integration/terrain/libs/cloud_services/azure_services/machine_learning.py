from azure.mgmt.machinelearningcompute import MachineLearningComputeManagementClient


class MachineLearning(object):
    service_name = 'machine learning'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = MachineLearningComputeManagementClient(credentials=self.platform.credentials,
                                                        subscription_id=self.platform.subscription_id)
        operations = client.machine_learning_compute.list_available_operations()
        assert len(operations.value) > 0