# coding: utf-8
"""
Created on 07.08.18
@author: Eugeny Kurkovich
"""
import pytest
import requests

from api.utils.helpers import uniq_uuid
from api.utils.consts import Platform, COST_PROJECT_ID, ENV_ID


class Setup(object):

    api = None
    env_id = ENV_ID
    cost_project_id = COST_PROJECT_ID
    role_id = 57039

    def init_api(self, api):
        if not self.__class__.api:
            self.__class__.api = api
        return self.__class__.api

    def create_farm(self, name=None, project_id=None,
                    farm_tpl=None, return_status_code=False, **kwargs):
        name = name or self.uniq_farm_name
        project_id = project_id or self.cost_project_id

        body = dict(
            name=name,
            project={"id": project_id},
            **kwargs
        )
        resp = self.api.create(
            "/api/v1beta0/user/envId/farms/",
            params=dict(envId=self.env_id),
            body=farm_tpl or body)
        if return_status_code:
            res = resp.status_code
        else:
            res = resp.json_data.data
        return res

    def add_role_to_farm(self, farm_id, alias,
                         location, platform,
                         instance_type_id, role_id,
                         network, zone, **kwargs):
        body = dict(
            alias=alias,
            cloudLocation=location,
            cloudPlatform=platform,
            instanceType={'id': instance_type_id},
            availabilityZones=[zone],
            role={'id': role_id},
            networking={'networks': [{'id': network}]},
            **kwargs
        )

        resp = self.api.create(
            "/api/v1beta0/user/envId/farms/farmId/farm-roles/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            ),
            body=body)

        return resp.json_data.data

    def gen_farm_template(self, farm_id, farm_name=None):
        tpl = self.api.generate_template(
            "/api/v1beta0/user/envId/farms/farmId/actions/generate-template/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )).json_data.data
        if farm_name:
            tpl.farm.name = farm_name
        return tpl

    def get_farm(self, farm_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/farms/farmId/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )
        )
        return resp.json_data.data

    def get_role(self, role_id):
        resp = self.api.get(
            "/api/v1beta0/user/envId/roles/roleId/",
            params=dict(
                envId=self.env_id,
                roleId=role_id
            )
        )
        return resp.json_data.data

    def get_farm_roles(self, farm_id):
        resp = self.api.list(
            "/api/v1beta0/user/envId/farms/farmId/farm-roles/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )
        )
        return resp.json_data.data

    @property
    def uniq_farm_name(self):
        return "tmp-api-%s" % uniq_uuid()


class TestEmptyFarm(Setup):

    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        # create empty Farm
        self.farm = self.create_farm()
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)
        self.role = self.get_role(self.role_id)

    def test_deploy_empty_farm(self):
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        # create Farm from template
        farm = self.create_farm(
            farm_tpl=farm_tpl.to_dict()
        )
        # check Farm created
        assert farm_tpl.farm.name == self.get_farm(farm_id=farm.id).name

    def test_deploy_farm_add_farm_role(self):
        farm_tpl = self.farm_tpl.copy()
        # modify farm template
        farm_tpl.farm.name = self.uniq_farm_name
        # add role to farm template
        role_params = dict(
            cloudLocation=Platform.GCE.location,
            cloudPlatform=Platform.GCE,
            instanceType={'id': Platform.GCE.instance_type},
            role=dict(id=self.role.id),
            alias=self.role.name,
            availabilityZones=[Platform.GCE.zone],
            networking={'networks': [{'id': Platform.GCE.network}]}
        )
        farm_tpl.roles.append(role_params)
        # create Farm from template
        farm = self.create_farm(
            farm_tpl=farm_tpl.to_dict()
        )
        # check Farm created
        assert farm_tpl.farm.name == self.get_farm(farm_id=farm.id).name
        assert self.get_farm_roles(farm.id)

    def test_deploy_existing_farm(self):
        # create Farm from template
        exc_message = "'FarmTemplate.farm.name' ({farm_name}) already exists. " \
                      "The 'id' is ({farm_id})".format(
            farm_name=self.farm.name,
            farm_id=self.farm.id
        )
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(
                farm_tpl=self.farm_tpl.to_dict())
        assert exc_message in e.value.args[0]


class TestSimpleFarm(Setup):


    def change_role_deprecated_state(self, role_id, deprecated=True):
        body = dict(deprecate=deprecated)
        resp = self.api.deprecate(
            "/api/v1beta0/user/envId/roles/roleId/actions/deprecate/",
            params=dict(
                envId=self.env_id,
                roleId=role_id),
            body=body)
        return resp.json_data.data


    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        self.role = self.get_role(self.role_id)
        # create empty Farm
        self.farm = self.create_farm()
        # add GCE role to farm by api call
        self.add_role_to_farm(
            farm_id=self.farm.id,
            alias=self.role.name,
            location=Platform.GCE.location,
            platform=Platform.GCE,
            instance_type_id=Platform.GCE.instance_type,
            zone=Platform.GCE.zone,
            network=Platform.GCE.network,
            role_id=self.role.id
        )
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=self.farm.id)

    def test_deploy_farm_invalid_tpl_structure(self):
        exc_message = "InvalidStructure: 'Farm.data' does not exist."
        farm_tpl = {'data': self.farm_tpl.copy()}
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message == e.value.args[0]

    def test_deploy_farm_invalid_cost_project_id(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.farm.project.id' ({project_id}) was not found."
        farm_tpl = self.farm_tpl.copy()
        # set invalid project id
        farm_tpl.farm.project.id = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(project_id=farm_tpl.farm.project.id) == e.value.args[0]

    def test_deploy_farm_invalid_role_id(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.roles.id' ({role_id}) was not found " \
                      "or isn't in scope for the current Environment."
        farm_tpl = self.farm_tpl.copy()
        # set invalid role id
        farm_tpl.roles[0].role.id = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(role_id=farm_tpl.roles[0].role.id) == e.value.args[0]

    def test_deploy_farm_invalid_role_name(self):
        exc_message = "ObjectNotFound: 'FarmTemplate.roles.name' ({role_name}) was not found " \
                      "or isn't in scope for the current Environment."
        farm_tpl = self.farm_tpl.copy()
        # set invalid role name
        farm_tpl.roles[0].role.name = uniq_uuid()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(role_name=farm_tpl.roles[0].role.name) == e.value.args[0]

    def test_deploy_farm_deprecated_role(self):
        exc_message = "Deprecated: 'FarmTemplate.roles.role.id' ({role_id}) is deprecated."
        # set role deprecated
        self.change_role_deprecated_state(self.role.id)
        farm_tpl = self.farm_tpl.copy()
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(role_id=self.role.id) == e.value.args[0]
        # unset role deprecated
        self.change_role_deprecated_state(self.role.id, deprecated=False)

    def test_deploy_farm_invalid_cloud_platform(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.cloudPlatform ({platform}) is invalid."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.roles[0].cloudPlatform = Platform.INVALID
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(platform=Platform.INVALID) == e.value.args[0]

    def test_deploy_farm_invalid_cloud_location(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.cloudLocation' ({location}) is invalid " \
                      "for 'FarmRole.alias' ({name})."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].cloudLocation = Platform.INVALID.location
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(location=Platform.INVALID.location, name=self.role.name) == e.value.args[0]

    def test_deploy_farm_invalid_zone(self):
        exc_message = "ObjectNotFoundOnCloud: 'FarmTemplate.roles.availabilityZones' ({zone}) was not found in the cloud."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].availabilityZones[0] = Platform.INVALID.zone
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(zone=Platform.INVALID.zone) in e.value.args[0]

    def test_deploy_farm_invalid_instance_type(self):
        exc_message = "InvalidValue: 'FarmTemplate.roles.instanceType.id' ({type}) is invalid."
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = Platform.INVALID.instance_type
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(type=Platform.INVALID.instance_type) == e.value.args[0]

    def test_deploy_farm_invalid_instance_cpu_count(self):
        exc_message = "InvalidValue: Custom 'FarmTemplate.roles.instanceType' ({cpu}) CPU count 0 is invalid."
        custom_cpu = 'custom-0-0'
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = custom_cpu
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(cpu=custom_cpu) in e.value.args[0]

    def test_deploy_farm_invalid_instance_memory_size(self):
        exc_message = "InvalidValue: Custom 'FarmTemplate.roles.instanceType' ({ram}) memory size 0 is invalid."
        custom_ram = 'custom-1-0'
        farm_tpl = self.farm_tpl.copy()
        farm_tpl.farm.name = self.uniq_farm_name
        farm_tpl.roles[0].instanceType.id = custom_ram
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_farm(farm_tpl=farm_tpl)
        assert exc_message.format(ram=custom_ram) in e.value.args[0]
