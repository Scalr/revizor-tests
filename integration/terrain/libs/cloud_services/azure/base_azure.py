from azure.common.credentials import ServicePrincipalCredentials

from integration.terrain.libs.cloud_services import CloudServiceBase
from revizor2.utils import env_vars


class AzureCloudService(CloudServiceBase):
    """
    Base class for Azure services.
    Contains Azure-specific logic that is common for all services
    """
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']
    resource_group_name = 'revizor'

    def __init__(self, request_id, secret):
        super(AzureCloudService, self).__init__(request_id, secret)
        self.credentials = None
        self.subscription_id = None

    def configure(self):
        super(AzureCloudService, self).configure()
        self.subscription_id = self.request['cc_id']
        with env_vars(https_proxy='http://%s' % self.csg_proxy,
                      REQUESTS_CA_BUNDLE=self.cacert_path):
            self.credentials = ServicePrincipalCredentials(
                client_id=self.request['client_id'],
                secret=self.secret,
                tenant=self.request['tenant_id']
            )

    def verify(self):
        with env_vars(https_proxy='http://%s' % self.csg_proxy,
                      REQUESTS_CA_BUNDLE=self.cacert_path):
            self._verify_impl()

    def _verify_impl(self):
        raise NotImplementedError()
