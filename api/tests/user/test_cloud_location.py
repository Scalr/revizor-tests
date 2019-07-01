import pytest
import requests


class TestCloudLocation(object):
    env_id = "5"
    cloud_platform = "ec2"
    cloud_location = "us-east-1"
    instance_type_id = "t1.micro"

    def test_cloud_location_list(self, api):
        # Execute request
        resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/",
            params=dict(
                envId=self.env_id,
                cloudPlatform=self.cloud_platform))
        assert resp.json()['data'][0]['cloudLocation'] == self.cloud_location

    def test_cloud_location_list_invalid_cloud_platform(self, api):
        invalid_cloud_platform = "qwert"
        exc_message = f"Requested 'cloudPlatform' ({invalid_cloud_platform}) was not found."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/",
            params=dict(
                envId=self.env_id,
                cloudPlatform=invalid_cloud_platform))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text

    def test_cloud_location_list_invalid_envId(self, api):
        invalid_envId = 4
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/",
            params = dict(
                envId=invalid_envId,
                cloudPlatform=self.cloud_platform))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    def test_cloud_location_list_noaccess_envId(self, api):
        noaccess_envId = 13
        exc_message = "You don't have access to the environment." 
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/",
            params = dict(
                envId=noaccess_envId,
                cloudPlatform=self.cloud_platform))
        assert err.value.response.status_code == 403
        assert exc_message in err.value.response.text

    def test_instance_types_list(self, api):
       # Execute request
        resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/cloudLocation/instance-types/",
            params=dict(
                envId=self.env_id,
                cloudPlatform=self.cloud_platform,
                cloudLocation=self.cloud_location),
                filters=dict(id=self.instance_type_id))
        assert resp.json()['data'][0]['id'] == self.instance_type_id
    
    def test_instance_types_list_invalid_envId(self, api):
       # Execute request
        invalid_envId = 4
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/cloudLocation/instance-types/",
            params=dict(
                envId=invalid_envId,
                cloudPlatform=self.cloud_platform,
                cloudLocation=self.cloud_location))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    def test_instance_types_list_noaccess_envId(self, api):
       # Execute request
        noaccess_envId = 13
        exc_message = "You don't have access to the environment."    
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/cloudLocation/instance-types/",
            params=dict(
                envId=noaccess_envId,
                cloudPlatform=self.cloud_platform,
                cloudLocation=self.cloud_location))
        assert err.value.response.status_code == 403
        assert exc_message in err.value.response.text    
    
    def test_instance_types_list_invalid_cloud_platform(self, api):
        invalid_cloud_platform = "qwert"
        exc_message = f"Requested 'cloudPlatform' ({invalid_cloud_platform}) was not found."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/cloudLocation/instance-types/",
            params=dict(
                envId=self.env_id,
                cloudPlatform=invalid_cloud_platform,
                cloudLocation=self.cloud_location))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text

    def test_instance_types_list_invalid_cloud_location(self, api):
        invalid_cloud_location = "east-1"
        exc_message = f"Requested cloudLocation '{invalid_cloud_location}' does not exist."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/clouds/cloudPlatform/cloud-locations/cloudLocation/instance-types/",
            params=dict(
                envId=self.env_id,
                cloudPlatform=self.cloud_platform,
                cloudLocation=invalid_cloud_location))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text