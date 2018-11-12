import uuid

import pytest
import requests


INVALID_CREDS_LIST = [
    ({
        'accountName': 'testacc',
        'clientId': 'clientId',
        'privateKey': 'dsfsdfsd',
        'projectId': 'project1',
        'cloudCredentialsType': 'GceCloudCredentials',
        'description': 'created gce creds',
        'name': 'newgce'
    }, 'Failed to verify your GCE credentials'),
    ({
        'accessKey': 'dsfsdfsdfsdf',
        'secretKey': 'vxcvfsdfsdfs',
        'accountType': 'regular',
        'cloudCredentialsType': 'AwsCloudCredentials',
        'name': 'newec2'
    }, 'The AWS Access Key Id you provided does not exist in our records'),
    ({
        'apiKey': 'sdfsfsafsd',
        'secretKey': 'vxcvsdfsdfs',
        'name': 'cloudstacknew',
        'apiUrl': 'http://cloudstack.com',
        'cloudCredentialsType': 'CloudstackCloudCredentials',
        'provider': 'cloudstack',
    }, "Can\'t determine account name for provided keys."),
    ({
        'cloudCredentialsType': 'OpenstackCloudCredentials',
        'keystoneUrl': 'https://identity.api.rackspacecloud.com/v2.0',
        'name': 'new openstack',
        'password': 'dsfsdfsdfsdfs',
        'provider': 'openstack',
        'tenantName': 'tenant',
        'userName': 'user',
    }, 'OpenStack error. Unable to authenticate user with credentials provided.'),
    ({
        'cloudCredentialsType': 'AzureCloudCredentials',
        'name': 'myazure',
        'subscription': 'subscr123',
        'tenantId': 'tenantId',
    }, 'MS Azure allows only OAuth authentication'),
    # ({
    #     'cloudCredentialsType': 'VmwareCloudCredentials',
    #     'name': 'myvmware',
    #     'password': 'testpass',
    #     'url': 'https://vcenter2.dev.vmware.scalr.cloud',
    #     'userName': 'mysusername'
    # }, 'dfsdfs')
    # TIPS: VMWare very slow and disabled
]


class TestCloudCredentials:

    def test_list_cc(self, api):
        cc = api.list('/api/v1beta0/global/cloud-credentials/').json()
        # In test env 9 cc on global scope
        assert len(cc['data']) >= 9

    def test_get_cc(self, api): # check all credential types
        all_cc = api.list('/api/v1beta0/global/cloud-credentials/').json()
        cc = all_cc['data'][0]
        get_cc = api.get('/api/v1beta0/global/cloud-credentials/cloudCredentialsId/', params={
            'cloudCredentialsId': cc['id']
        }).json()
        for field in cc:
            assert field in get_cc['data']
            assert cc[field] == get_cc['data'][field]

    def test_get_invalid_cc(self, api):
        with pytest.raises(requests.HTTPError) as err:
            api.get('/api/v1beta0/global/cloud-credentials/cloudCredentialsId/', params={
                'cloudCredentialsId': uuid.uuid4().hex[:12]
            })
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == 'ObjectNotFound'

    def test_edit_cc(self, api):
        all_cc = api.list('/api/v1beta0/global/cloud-credentials/').json()
        cc = all_cc['data'][0]
        edit_resp = api.edit('/api/v1beta0/global/cloud-credentials/cloudCredentialsId/', params={
            'cloudCredentialsId': cc['id']
        }, body={
            'name': 'My edit CC',
            'description': 'Check edit credentials',
        }).json()
        assert edit_resp['data']['name'] == 'My edit CC'
        assert edit_resp['data']['description'] == 'Check edit credentials'

    def test_delete_cc_in_use(self, api):
        all_cc = api.list('/api/v1beta0/global/cloud-credentials/').json()
        with pytest.raises(requests.HTTPError) as err:
            api.delete('/api/v1beta0/global/cloud-credentials/cloudCredentialsId/', params={
                'cloudCredentialsId': all_cc['data'][0]['id']
            })
        assert err.value.response.status_code == 409
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == 'ObjectInUse'
        assert len(all_cc['data']) == len(api.list('/api/v1beta0/global/cloud-credentials/').json()['data'])

    def test_delete_invalid_cc(self, api):
        all_cc = api.list('/api/v1beta0/global/cloud-credentials/').json()
        with pytest.raises(requests.HTTPError) as err:
            api.delete('/api/v1beta0/global/cloud-credentials/cloudCredentialsId/', params={
                'cloudCredentialsId': uuid.uuid4().hex[:12]
            })
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == 'ObjectNotFound'
        assert len(all_cc['data']) == len(api.list('/api/v1beta0/global/cloud-credentials/').json()['data'])

    @pytest.mark.parametrize('cloud_body,errmsg', INVALID_CREDS_LIST)
    def test_create_invalid_cc(self, api, cloud_body, errmsg):
        errcode = 400
        if cloud_body['cloudCredentialsType'] == 'AzureCloudCredentials':
            errcode = 501
        with pytest.raises(requests.HTTPError) as err:
            api.create('/api/v1beta0/global/cloud-credentials/', body=cloud_body)
        assert errmsg in err.value.response.text
        assert err.value.response.status_code == errcode
