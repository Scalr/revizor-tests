class TestOs(object):

    env_id = "5"
    os_id = "ubuntu-14-04"

    def test_os_list(self, api):
        # Execute request
        resp = api.list(
            "/api/v1beta0/user/envId/os/",
            params=dict(envId=self.env_id),
            filters=dict(id=self.os_id))
        assert resp.json()['data'][0]['id'] == self.os_id

    def test_os_get(self, api):
        # Execute request
        resp = api.get(
            "/api/v1beta0/user/envId/os/osId/",
            params=dict(
                envId=self.env_id,
                osId=self.os_id))
        assert resp.json()['data']['id'] == self.os_id
