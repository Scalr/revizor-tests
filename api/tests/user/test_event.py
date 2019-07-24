import pytest
import requests

class TestEventsUserScope(object):
    env_id = "5"
    event_id = "BeforeInstanceLaunch"
    scope = "scalr"

    def test_events_create(self,api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                description = "test event",
                id = "create event"
                ))
        return create_resp.box().data

    def test_events_list(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                description = "test event",
                id = "list event"))
        resp_event_id = create_resp.json()['data']['id']
        resp = api.list(
            "/api/v1beta0/user/envId/events/",
            params=dict(
                envId=self.env_id))
        assert resp.json()['data'][0]['id'] == resp_event_id
    
    def test_events_list_filters(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            filters=dict(scope=self.scope))
        assert resp.json()['data'][0]['id'] == self.event_id

    def test_event_list_invalid_envId(self, api):
        invalid_envId = 4
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/user/envId/events/",
            params=dict(
                envId=invalid_envId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text