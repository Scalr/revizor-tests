import pytest
import requests

class TestRoleCategoriesUserScope(object):
    env_id = "5"
    role_categories_id = 1
    
    #test list
    def test_userscope_role_categories_list(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/role-categories/",
            params=dict(
                envId=self.env_id),
                filters=dict(id=self.role_categories_id))
        assert resp.json()['data'][0]['id'] == self.role_categories_id

    def test_userscope_role_categories_list_invalid_envId(self, api):
        invalid_envId = 4
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/user/envId/role-categories/",
            params=dict(
                envId=invalid_envId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    def test_userscope_role_categories_list_noassecc_envId(self, api):
        noaccess_envId = 13
        exc_message = "You don't have access to the environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/user/envId/role-categories/",
            params=dict(
                envId=noaccess_envId))
        assert err.value.response.status_code == 403
        assert exc_message in err.value.response.text

    #test get
    def test_userscope_role_categories_get(self, api):
        resp = api.list(
            "/api/v1beta0/user/envId/role-categories/roleCategoryId/",
            params=dict(
                envId=self.env_id,
                roleCategoryId=self.role_categories_id))
        assert resp.json()['data']['id'] == self.role_categories_id 

    def test_userscope_role_categories_get_invalid_rolecategoriesId(self, api):
        invalid_rolecategoriesId = 99999
        exc_message = f"'RoleCategory.id' ({invalid_rolecategoriesId}) either was not found or isn't from current scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/user/envId/role-categories/roleCategoryId/",
            params=dict(
                envId=self.env_id,
                roleCategoryId=invalid_rolecategoriesId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text   

    #test edit
    def test_userscope_role_categories_edit(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/role-categories/",
            params=dict(envId=self.env_id),
            body=dict(
                name= "my category"
                ))
        id_cat = create_resp.json()['data']['id']
        edit_resp = api.edit("/api/v1beta0/user/envId/role-categories/roleCategoryId/",
            params=dict(
            envId=self.env_id,
            roleCategoryId=id_cat 
        ), body=dict(
            name= "edit category"
        ))
        assert edit_resp.json()['data']['name'] == "edit category"

    #test create
    def test_userscope_role_categories_create(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/role-categories/",
            params=dict(envId=self.env_id),
            body=dict(
                name = "user category"
                ))
        return create_resp.box().data

    def test_userscope_role_categories_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/role-categories/",
            params=dict(envId=self.env_id),
            body=dict(
                name = "test category"
                ))
        name_duplicate = create_resp.json()['data']['name'] 
        exc_message = f"'RoleCategory.name' ({name_duplicate}) already exists."
        with pytest.raises(requests.exceptions.HTTPError) as err: 
            create_resp = api.create("/api/v1beta0/user/envId/role-categories/",
                params=dict(envId=self.env_id),
                body=dict(
                name = name_duplicate
                  ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text

    #test delete
    def test_userscope_role_categories_delete(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/role-categories/",
            params=dict(envId=self.env_id),
            body=dict(
                name = "delete category"
                ))
        id_cat = create_resp.json()['data']['id']
        delete_resp = api.delete("/api/v1beta0/user/envId/role-categories/roleCategoryId/",
            params=dict(
                envId=self.env_id,
                roleCategoryId=id_cat
                ))
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.get("/api/v1beta0/user/envId/role-categories/roleCategoryId/",
                params=dict(
                    envId=self.env_id,
                    roleCategoryId=id_cat))
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"


class TestRoleCategoriesAccountScope(object):
    account_id = "1"
    role_categories_id = 1

    #test list
    def test_accountscope_role_categories_list(self, api):
        resp = api.list(
            "/api/v1beta0/account/accountId/role-categories/",
            params=dict(
                accountId=self.account_id))
        assert resp.json()['data'][0]['id'] == self.role_categories_id 

    def test_accountscope_role_categories_list_invalid_accountId(self, api):
        invalid_accountId = 2
        exc_message = "Invalid account."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/account/accountId/role-categories/",
            params=dict(
                accountId=invalid_accountId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    def test_accountscope_role_categories_list_noaccess_accountId(self, api):
        noaccess_accountId = 3
        exc_message = f"You don't have access to the account with ID '{noaccess_accountId}'."
        with pytest.raises(requests.exceptions.HTTPError) as err:
           resp = api.list(
            "/api/v1beta0/account/accountId/role-categories/",
            params=dict(
                accountId=noaccess_accountId))
        assert err.value.response.status_code == 403
        assert exc_message in err.value.response.text 

    #test get
    def test_accountscope_role_categories_get(self, api):
        resp = api.list(
            "/api/v1beta0/account/accountId/role-categories/roleCategoryId/",
            params=dict(
                accountId=self.account_id,
                roleCategoryId=self.role_categories_id))
        assert resp.json()['data']['id'] == self.role_categories_id

    def test_accountscope_role_categories_get_invalid_rolecategoriesId(self, api):
        invalid_rolecategoriesId = 99999
        exc_message = f"'RoleCategory.id' ({invalid_rolecategoriesId}) either was not found or isn't from current scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/account/accountId/role-categories/roleCategoryId/",
            params=dict(
                accountId=self.account_id,
                roleCategoryId=invalid_rolecategoriesId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text 

    #test edit
    def test_accountscope_role_categories_edit(self, api):
        create_resp = api.create("/api/v1beta0/account/accountId/role-categories/",
            params=dict(accountId=self.account_id),
            body=dict(
                name= "my category"
                ))
        id_cat = create_resp.json()['data']['id'] 
        edit_resp = api.edit("/api/v1beta0/account/accountId/role-categories/roleCategoryId/",
            params=dict(
                accountId=self.account_id,
                roleCategoryId=id_cat),
            body=dict(
                name= "edit category"
                ))
        assert edit_resp.json()['data']['name'] == "edit category"

    #test create
    def test_accountscope_role_categories_create(self, api):
        create_resp = api.create("/api/v1beta0/account/accountId/role-categories/",
            params=dict(accountId=self.account_id),
            body=dict(
                name = "account category"
                ))
        return create_resp.box().data

    def test_accountscope_role_categories_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/account/accountId/role-categories/",
            params=dict(accountId=self.account_id),
            body=dict(
                name = "test category"
                ))
        name_duplicate = create_resp.json()['data']['name'] 
        exc_message = f"'RoleCategory.name' ({name_duplicate}) already exists."
        with pytest.raises(requests.exceptions.HTTPError) as err: 
            create_resp = api.create("/api/v1beta0/account/accountId/role-categories/",
                params=dict(accountId=self.account_id),
                body=dict(
                name = name_duplicate
                  ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text

    #test delete
    def test_accountscope_role_categories_delete(self, api):
        create_resp = api.create("/api/v1beta0/account/accountId/role-categories/",
            params=dict(accountId=self.account_id),
            body=dict(
                name = "delete category"
                ))
        id_cat = create_resp.json()['data']['id']
        delete_resp = api.delete("/api/v1beta0/account/accountId/role-categories/roleCategoryId/",
            params=dict(
                accountId=self.account_id,
                roleCategoryId=id_cat
                ))
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.get("/api/v1beta0/account/accountId/role-categories/roleCategoryId/",
                params=dict(
                    accountId=self.account_id,
                    roleCategoryId=id_cat))
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"
        

class TestRoleCategoriesAdminScope(object):
    role_categories_id = 1    

    #test list
    def test_adminscope_role_categories_list(self, api):
        resp = api.list(
            "/api/v1beta0/global/role-categories/")
        assert resp.json()['data'][0]['id'] == self.role_categories_id 

    #test get
    def test_adminscope_role_categories_get(self, api):
        resp = api.list(
            "/api/v1beta0/global/role-categories/roleCategoryId/",
            params=dict(
                roleCategoryId=self.role_categories_id))
        assert resp.json()['data']['id'] == self.role_categories_id 

    def test_admintscope_role_categories_get_invalid_rolecategoriesId(self, api):
        invalid_rolecategoriesId = 99999
        exc_message = f"'RoleCategory.id' ({invalid_rolecategoriesId}) either was not found or isn't from current scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list(
            "/api/v1beta0/global/role-categories/roleCategoryId/",
            params=dict(
                roleCategoryId=invalid_rolecategoriesId))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text 

    #test edit
    def test_adminscope_role_categories_edit(self, api):
        create_resp = api.create("/api/v1beta0/global/role-categories/",
            body=dict(
                name= "my category"
                ))
        id_cat = create_resp.json()['data']['id'] 
        edit_resp = api.edit("/api/v1beta0/global/role-categories/roleCategoryId/",
            params=dict(
            roleCategoryId=id_cat
        ), body=dict(
            name= "edit category"
        ))
        assert edit_resp.json()['data']['name'] == "edit category"
    
    #test create
    def test_adminscope_role_categories_create(self, api):
        create_resp = api.create("/api/v1beta0/global/role-categories/",
            body=dict(
                name= "admin category"
                ))
        return create_resp.box().data

    def test_adminscope_role_categories_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/global/role-categories/",
            body=dict(
                name = "test category"
                ))
        name_duplicate = create_resp.json()['data']['name'] 
        exc_message = f"'RoleCategory.name' ({name_duplicate}) already exists."
        with pytest.raises(requests.exceptions.HTTPError) as err: 
            create_resp = api.create("/api/v1beta0/global/role-categories/",
                body=dict(
                    name = name_duplicate
                  ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text 

    #test delete
    def test_adminscope_role_categories_delete(self, api):
        create_resp = api.create("/api/v1beta0/global/role-categories/",
            body=dict(
                name = "delete category"
                ))
        id_cat = create_resp.json()['data']['id']
        delete_resp = api.delete('/api/v1beta0/global/role-categories/roleCategoryId/',
            params=dict(
                roleCategoryId=id_cat
                ))
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.get("/api/v1beta0/global/role-categories/roleCategoryId/",
                params=dict(
                    roleCategoryId=id_cat))
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"