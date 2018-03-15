from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient


class Insights(object):
    service_name = 'insights'
    log_records = ['https://login.microsoftonline.com']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = ApplicationInsightsManagementClient(credentials=self.platform.credentials,
                                                     subscription_id=self.platform.subscription_id)
