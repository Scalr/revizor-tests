import pytest
import requests

class TestEventsUserScope(object):
    env_id = "5"

    #test create
    def test_events_create(self,api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                description = "test event",
                id = "create"
                ))
        return create_resp.box().data

    def test_role_events_create_id_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                id = "duplicate"
                ))
        name_duplicate = create_resp.json()['data']['id'] 
        exc_message = f"'Event.id' ({name_duplicate}) already exists in the scope (Environment)."
        with pytest.raises(requests.exceptions.HTTPError) as err: 
            create_resp = api.create("/api/v1beta0/user/envId/events/",
                params=dict(envId=self.env_id),
                body=dict(
                  id = name_duplicate
                  ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text

    def test_role_events_create_id_invalid(self, api):
        exc_message = "(create events) is invalid. Identifier has to match the pattern "
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create( "/api/v1beta0/user/envId/events/",
                params=dict(envId=self.env_id),
                body=dict(
                   id = "create events"
                ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text

    #test list
    def test_events_list(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/events/",
            params=dict(
                envId=self.env_id))
        assert resp.json()['data'][0]['id'] 

    def test_events_list_invalid_envId(self, api):
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/user/envId/events/",
            params=dict(
                envId=4 ))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    #test get
    def test_events_get(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                description = "test event",
                id = "events"
                ))
        id_events = create_resp.json()['data']['id']
        get_resp = api.get(
            "/api/v1beta0/user/envId/events/eventId/",
            params=dict(
                envId=self.env_id,
                eventId=id_events))
        assert get_resp.json()['data']['id'] == id_events
   
    def test_events_get_invalid_eventId(self, api):
        exc_message = "(999999999) either was not found or isn't in the current scope (Environment)."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/events/eventId/",
            params=dict(
                envId=self.env_id,
                eventId=999999999))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text
    
    #test delete
    def test_events_delete(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                id = "delete"
                ))
        id_events = create_resp.json()['data']['id']
        delete_resp = api.delete("/api/v1beta0/user/envId/events/eventId/",
            params=dict(
                envId=self.env_id, 
                eventId= id_events))
        with pytest.raises(requests.exceptions.HTTPError) as err:
            get_resp = api.get("/api/v1beta0/user/envId/events/eventId/",
            params=dict(
                envId=self.env_id,
                eventId=id_events))
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"

    def test_events_delete_invalid_eventid(self,api):
        exc_message = "(999999999999) either was not found or isn't in the current scope (Environment)."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            delete_resp = api.delete("/api/v1beta0/user/envId/events/eventId/",
                params=dict(
                    envId=self.env_id, 
                    eventId= 999999999999))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text 
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"
    
    #test edit . не работает 
    def test_events_edit(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/events/",
            params=dict(envId=self.env_id),
            body=dict(
                description= "exensts",
                id= "edit"
                ))
        id_events = create_resp.json()['data']['id']
        edit_resp = api.edit("/api/v1beta0/user/envId/events/eventId/",
            params=dict(
               envId=self.env_id,
               eventId=id_events),
            body=dict(
                  description= "test"
               ))
        assert edit_resp.json()['data']['description'] == "test"
   
        