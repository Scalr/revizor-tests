from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient


class Insights(object):
    service_name = 'insights'
    log_records = ['CONNECT login.microsoftonline.com:443',
                   'CONNECT management.azure.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = ApplicationInsightsManagementClient(credentials=self.platform.credentials,
                                                     subscription_id=self.platform.subscription_id)
