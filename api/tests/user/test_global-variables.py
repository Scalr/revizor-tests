import pytest
import requests


class TestGlobalVariablesUserScope(object):
    env_id = "5"
    
    #test create GlobalVariablesString
    def test_global_variablesString_create_hiddenlocked_true(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=True,
                locked=True,
                description="desc",
                outputFormat="%&",
                type="GlobalVariableString",
                validationPattern="/test/",
                value="/test/",
                name="NewGV"
                ))
        assert create_resp.json()['data']['hidden'] == True
        assert create_resp.json()['data']['locked'] == True
        assert create_resp.json()['data']['type'] == "GlobalVariableString"
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['definedIn'] == "environment"
  
    def test_global_variablesString_create_hiddenlocked_false(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=False,
                locked=False,
                description="desc",
                outputFormat="%&",
                type="GlobalVariableString",
                validationPattern="/test/",
                value="/test/",
                name="Allfalse"
                ))
        assert create_resp.json()['data']['hidden'] == False
        assert create_resp.json()['data']['locked'] == False
        assert create_resp.json()['data']['type'] == "GlobalVariableString"
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['definedIn'] == "environment"
    
    def test_global_variablesString_create_hidden_true_locked_false(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=True,
                locked=False,
                description="desc",
                outputFormat="%&",
                type="GlobalVariableString",
                validationPattern="/test/",
                value="/test/",
                name="truefalse"
                ))
        assert create_resp.json()['data']['hidden'] == True
        assert create_resp.json()['data']['locked'] == False
        assert create_resp.json()['data']['type'] == "GlobalVariableString"
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['definedIn'] == "environment"
   
    def test_global_variablesString_create_hidden_false_locked_true(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=False,
                locked=True,
                description="desc",
                outputFormat="%&",
                type="GlobalVariableString",
                validationPattern="/test/",
                value="/test/",
                name="true_false"
                ))
        assert create_resp.json()['data']['hidden'] == False
        assert create_resp.json()['data']['locked'] == True
        assert create_resp.json()['data']['type'] == "GlobalVariableString"
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['definedIn'] == "environment"
    
    def test_global_variablesString_create_required_farmcope(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                requiredIn="farm",
                description="desc",
                outputFormat="%&",
                type="GlobalVariableString",
                validationPattern="/test/",
                value="/test/",
                name="farmscoprequired"
                ))
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['requiredIn'] == "farm"
        assert create_resp.json()['data']['type'] == "GlobalVariableString"
   
    def test_global_variablesString_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableString",
                name="duplicate"
                ))
        name_duplicate = create_resp.json()['data']['name']
        exc_message = "'GlobalVariable.name' (duplicate) already exists on (Environment) scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create.resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
            type="GlobalVariableString",
            name=name_duplicate
            ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text
    
    def test_global_variablesString_create_invalid_value(self, api):
        exc_message = "\'GlobalVariable.value\'(\\/GV\\/) doesn\'t match to \'validationPattern\' (\\/test\\/)"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    description="desc",
                    outputFormat="%&",
                    type="GlobalVariableString",
                    validationPattern="/test/",
                    value="/GV/",
                    name="invalidValue"
                    ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    def test_global_variablesString_create_invalid_format(self, api):
        exc_message = "'GlobalVariable.outputFormat' (string) is invalid. Output format should consists of a percent sign %, followed by type specifier."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="Farm",
                    description="desc",
                    outputFormat="string",
                    type="GlobalVariableString",
                    name="invalidValue"
                    ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    def test_global_variablesString_create_invalid_requiredIn(self, api):
        exc_message = "'GlobalVariable.requiredIn'(scalr) is invalid scope"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="scalr",
                    description="desc",
                    type="GlobalVariableString",
                    name="invalidrequired"
                    ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    def test_global_variables_create_invalid_type(self, api):
        exc_message = "'GlobalVariable.type' (GlobalVariable) is invalid. Valid type are (GlobalVariableString, GlobalVariableJson, GlobalVariableList, GlobalVariableRemoteList)."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="scalr",
                    description="desc",
                    outputFormat="string",
                    type="GlobalVariable",
                    name="invalidValue"
                ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    #test create GlobalVariableJson
    def test_global_variablesJson_create(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                description="desc",
                type="GlobalVariableJson",
                value= "{ \"global_variables\": \"json\" }",
                name="gvjson"
            ))
        assert create_resp.json()['data']['value'] == "{ \"global_variables\": \"json\" }" 
        assert create_resp.json()['data']['type'] == "GlobalVariableJson"
    
    def test_global_variablesJson_create_required_farmrolecope(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                requiredIn="farmrole",
                type="GlobalVariableJson",
                name="FarmrolescoprequiredJson"
                ))
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['requiredIn'] == "farmrole"
        assert create_resp.json()['data']['type'] == "GlobalVariableJson"
    
    def test_global_variablesJson_create_hiddenlocked_true(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=True,
                locked=True,
                description="desc",
                type="GlobalVariableJson",
                value="{ \"global_variables\": \"json\" }",
                name="alltruejson"
                ))
        assert create_resp.json()['data']['hidden'] == True
        assert create_resp.json()['data']['locked'] == True
        assert create_resp.json()['data']['type'] == "GlobalVariableJson"
        
    def test_global_variablesJson_create_hiddenlocked_false(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=False,
                locked=False,
                description="desc",
                type="GlobalVariableJson",
                value="{ \"global_variables\": \"json\" }",
                name="allfalsejson1"
                ))
        assert create_resp.json()['data']['hidden'] == False
        assert create_resp.json()['data']['locked'] == False 
        assert create_resp.json()['data']['type'] == "GlobalVariableJson"
    
    def test_global_variablesJson_create_invalid_value(self, api):
        exc_message = "'GlobalVariable.value' is invalid JSON."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                category="new",
                description="desc",
                type="GlobalVariableJson",
                value= "text",
                name="gvjsontext"
            ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    def test_global_variablesJson_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableJson",
                name="duplicatejson2"
                ))
        name_duplicate = create_resp.json()['data']['name']
        exc_message = "\'GlobalVariable.name\' (duplicatejson2) already exists on (Environment) scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
            type="GlobalVariableJson",
            name=name_duplicate
            ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text 
    
    def test_global_variablesJson_create_invalid_requiredIn(self, api):
        exc_message = "'GlobalVariable.requiredIn'(scalr) is invalid scope"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="scalr",
                    description="desc",
                    type="GlobalVariableJson",
                    name="invalidrequired"
                    ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    #test create GlobalVariableList
    def test_global_variablesList_create_hiddenlocked_true(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
            category="new",
                hidden=True,
                locked=True,
                description="desc",
                type="GlobalVariableList",
                name="typelist",
                allowedValues= [
                    {
                        "value": "value3",
                        "label": "3"
                    },
                    {
                        "value": "value2",
                        "label": "2"
                    },
                    {
                        "value": "value1",
                        "label": "1"
                    }
                ]
                ))
        assert create_resp.json()['data']['hidden'] == True
        assert create_resp.json()['data']['locked'] == True
        assert create_resp.json()['data']['type'] == "GlobalVariableList"
        assert create_resp.json()['data']['definedIn'] == "environment"
    
    def test_global_variableslist_create_hiddenlocked_false(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=False,
                locked=False,
                description="desc",
                type="GlobalVariableList",
                name="testcreateGV",
                allowedValues=[
                    {
                        "value": "value3",
                        "label": "3"
                    },
                    {
                        "value": "value2",
                        "label": "2"
                    },
                    {
                        "value": "value1",
                        "label": "1"
                    }
                ],
                value="value3"
                ))
        assert create_resp.json()['data']['hidden'] == False
        assert create_resp.json()['data']['locked'] == False
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['type'] == "GlobalVariableList"

    def test_global_variablesList_create_hidden_true_locked_false(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                hidden=True,
                locked=False,
                description="desc",
                type="GlobalVariableList",
                name="truefalselist",
                allowedValues= [
                    {
                        "value": "value",
                        "label": "3"
                    }
                ]
                ))
        assert create_resp.json()['data']['hidden'] == True
        assert create_resp.json()['data']['locked'] == False
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['type'] == "GlobalVariableList"
    
    def test_global_variableslist_create_hidden_false_locked_true(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableList",
                name="GVTrueFalse",
                hidden=False,
                locked=True,
                allowedValues=[
                    {
                        "value": "value",
                        "label": "3"
                    }
                ]                
                ))
        assert create_resp.json()['data']['hidden'] == False
        assert create_resp.json()['data']['locked'] == True
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['type'] == "GlobalVariableList"
    
    def test_global_variablesList_create_required_farmcope(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                requiredIn="farm",
                type="GlobalVariableList",
                name="farmscoperequiredl",
                allowedValues= [
                    {
                        "value": "value",
                        "label": "3"
                    }
                ],
                value="value"   
                ))
        assert create_resp.json()['data']['declaredIn'] == "environment"
        assert create_resp.json()['data']['requiredIn'] == "farm"
        assert create_resp.json()['data']['type'] == "GlobalVariableList"
    
    def test_global_variablesList_create_name_duplicate(self, api):
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableList",
                name="duplicateGV",
                allowedValues=[
                    {
                        "value": "value",
                        "label": "3"
                    }
                ]
                ))
        name_duplicate = create_resp.json()['data']['name']
        exc_message = "'GlobalVariable.name' (duplicateGV) already exists on (Environment) scope."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
            type="GlobalVariableList",
            name=name_duplicate,
            allowedValues=[
                    {
                        "value": "value",
                        "label": "3"
                    }
                ]
            ))
        assert err.value.response.status_code == 409
        assert exc_message in err.value.response.text
    
    def test_global_variablesList_create_invalid_value(self, api):
        exc_message = "value\' is invalid. Each \'value\' has to match the pattern \'\\/^(?=.{1,255}$)[a-zA-Z0-9-_.,=@ +*()]+$\\/\'"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="Farm",
                    description="desc",
                    type="GlobalVariableList",
                    name="invalidValueName",
                    allowedValues= [
                    {
                        "value": "^)))",
                        "label": "3"
                    }
                    ]
                ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    def test_global_variablesList_create_inconsistency_value(self, api):
        exc_message = "\'GlobalVariable.requiredIn\'(Farm) is invalid scope"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="Farm",
                    description="desc",
                    type="GlobalVariableList",
                    name="invalidValue",
                    allowedValues= [
                    {
                        "value": "value",
                        "label": "3"
                    }
                    ],
                    value="test"
                ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text    
    
    def test_global_variablesList_create_without_allowedValues(self, api):
        exc_message = "Property \'GlobalVariable.allowedValues.value\' is required."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    type="GlobalVariableList",
                    name="invalidValueGV",
                    allowedValues= [{}]
                ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text

    def test_global_variablesList_create_invalid_requiredIn(self, api):
        exc_message = "'GlobalVariable.requiredIn'(scalr) is invalid scope"
        with pytest.raises(requests.exceptions.HTTPError) as err:
            create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
                params=dict(envId=self.env_id),
                body=dict(
                    category="new",
                    requiredIn="scalr",
                    description="desc",
                    type="GlobalVariableList",
                    name="invalidrequiredGV",
                    allowedValues= [
                    {
                        "value": "value",
                        "label": "3"
                    }
                    ]
                    ))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text
    
    #test list
    def test_global_variables_list(self, api):
        resp = api.list("/api/v1beta0/user/envId/global-variables/",
           params=dict(
                envId=self.env_id))
        assert resp.json()['data'][0]['name']
    
    def test_global_variables_list_wrong_envid(self, api):
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list("/api/v1beta0/user/envId/global-variables/",
                params=dict(
                    envId=9999999))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text
    
    def test_global_variables_list_invalid_envid(self, api):
        exc_message = "Environment has not been provided with the request."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.list("/api/v1beta0/user/envId/global-variables/",
                params=dict(
                    envId=0))
        assert err.value.response.status_code == 400
        assert exc_message in err.value.response.text 
  
    #test get
    def test_global_variables_get(self, api):
        create_resp = api.create( "/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                category="new",
                description="desc",
                name="getcreatee",
                type="GlobalVariableString"
                ))
        Variable_Name = create_resp.json()['data']['name']
        get_resp = api.get("/api/v1beta0/user/envId/global-variables/globalVariableName/",
            params=dict(
                envId=self.env_id,
                globalVariableName=Variable_Name
            ))
        assert get_resp.json()['data']['name'] == Variable_Name

    def test_global_variables_get_invalid_VariableName(self, api):  
        exc_message = "'GlobalVariable.name' (VariableName) was not found."
        with pytest.raises(requests.exceptions.HTTPError) as err: 
            resp = api.get("/api/v1beta0/user/envId/global-variables/globalVariableName/",
            params=dict(
                envId=self.env_id,
                globalVariableName="VariableName"
                )) 
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text
    
    #test delete 
    def test_global_variables_delete(self, api): 
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableString",
                name="gv"
                ))
        VariableName = create_resp.json()['data']['name']
        delete_resp = api.delete('/api/v1beta0/user/envId/global-variables/globalVariableName/',
            params=dict(
                envId=self.env_id,
                globalVariableName=VariableName
                ))
        with pytest.raises(requests.exceptions.HTTPError) as err:
            resp = api.get("/api/v1beta0/user/envId/global-variables/globalVariableName/",
                params=dict(
                    envId=self.env_id,
                    globalVariableName=VariableName
                    ))
        assert err.value.response.status_code == 404
        errors = err.value.response.json()['errors']
        assert errors[0]['code'] == "ObjectNotFound"
    
    def test_global_variables_delete_invalid_envId(self, api): 
        create_resp = api.create("/api/v1beta0/user/envId/global-variables/",
            params=dict(envId=self.env_id),
            body=dict(
                type="GlobalVariableString",
                name="gvdelete"
                ))
        VariableName = create_resp.json()['data']['name']
        exc_message = "Invalid environment."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            delete_resp = api.delete('/api/v1beta0/user/envId/global-variables/globalVariableName/',
            params=dict(
                envId=999999999999,
                globalVariableName=VariableName
                ))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text
 
    def test_global_variables_delete_invalid_name(self, api): 
        exc_message = "'GlobalVariable.name' (999999999999) was not found."
        with pytest.raises(requests.exceptions.HTTPError) as err:
            delete_resp = api.delete('/api/v1beta0/user/envId/global-variables/globalVariableName/',
            params=dict(
                envId=self.env_id,
                globalVariableName=999999999999
                ))
        assert err.value.response.status_code == 404
        assert exc_message in err.value.response.text

    