from botocore import exceptions as boto_exceptions
from lettuce import world


class Pinpoint(object):
    service_name = 'pinpoint'
    log_records = ['CONNECT pinpoint.us-east-1.amazonaws.com:443']

    def __init__(self, platform):
        self.platform = platform

    def verify(self):
        client = self.platform.get_client('pinpoint')
        app_name, segment_name = self.platform.get_test_name('app', 'segment')
        app_id = client.create_app(
            CreateApplicationRequest={
                'Name': app_name
            })['ApplicationResponse']['Id']
        assert any([app for app in client.get_apps()['ApplicationsResponse']['Item'] if app['Name'] == app_name])
        assert client.get_app(ApplicationId=app_id)['ApplicationResponse']['Name'] == app_name
        segment_id = client.create_segment(
            ApplicationId=app_id,
            WriteSegmentRequest={'Name': segment_name}
        )['SegmentResponse']['Id']
        assert any([segment for segment in client.get_segments(ApplicationId=app_id)['SegmentsResponse']['Item']
                    if segment['Name'] == segment_name])
        assert client.get_segment(ApplicationId=app_id, SegmentId=segment_id)['SegmentResponse']['Name'] == segment_name
        client.delete_segment(ApplicationId=app_id, SegmentId=segment_id)
        with world.assert_raises(boto_exceptions.ClientError, 'NotFoundException'):
            client.get_segment(ApplicationId=app_id, SegmentId=segment_id)
        client.delete_app(ApplicationId=app_id)
        with world.assert_raises(boto_exceptions.ClientError, 'NotFoundException'):
            client.get_app(ApplicationId=app_id)
