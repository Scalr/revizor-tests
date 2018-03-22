class StreamAnalytics(object):
    service_name = 'stream analytics'
    log_records = []

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        pass

    def verify_denied(self, error_text):
        pass
