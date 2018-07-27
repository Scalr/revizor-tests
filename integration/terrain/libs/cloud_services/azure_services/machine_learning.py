from azure.mgmt.machinelearningcompute import MachineLearningComputeManagementClient
import azure.common.exceptions as az_exceptions
from lettuce import world


class MachineLearning(object):
    service_name = 'machine learning'
    log_records = ['https://login.microsoftonline.com',
                   'https://management.azure.com',
                   'providers/Microsoft.MachineLearningCompute']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = MachineLearningComputeManagementClient(credentials=self.platform.get_credentials(),
                                                        subscription_id=self.platform.subscription_id)
        operations = client.machine_learning_compute.list_available_operations()
        assert len(operations.value) > 0

    def verify_denied(self, error_text):
        with world.assert_raises(az_exceptions.ClientException, error_text):
            client = MachineLearningComputeManagementClient(credentials=self.platform.get_credentials(),
                                                            subscription_id=self.platform.subscription_id)
            client.machine_learning_compute.list_available_operations()
