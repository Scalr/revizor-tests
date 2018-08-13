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

    def create_farm(self, name=None, project_id=None, farm_tpl=None, **kwargs):
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

        return resp.json_data.data

    def add_role_to_farm(self, farm_id, alias,
                         location, platform,
                         instance_type_id, role_id, **kwargs):
        body = dict(
            alias=alias,
            cloudLocation=location,
            cloudPlatform=platform,
            instanceType={'id': instance_type_id},
            role={'id': role_id},
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
        tpl = self.api.get(
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

    @property
    def uniq_farm_name(self):
        return "tmp-api-%s" % uniq_uuid()


class TestEmptyFarm(Setup):

    @pytest.fixture(autouse=True)
    def bootstrap(self, api):
        self.api = super().init_api(api)
        # create empty Farm
        farm = self.create_farm()
        # gen tpl from Farm
        self.farm_tpl = self.gen_farm_template(
            farm_id=farm.id)
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

    def test_deploy_farm(self):
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


class TestGCEFarm(Setup):

    def test_farm_template_gce(self):
        # create empty Farm
        farm = self.create_farm()
        role_params = dict(
            farm_id=farm.id,
            alias=farm.name,
            location=Platform.GCE.location,
            platform=Platform.GCE,
            instance_type_id=Platform.GCE.instance_type,
            role_id=''
        )
        # add role to farm
        farm_role = self.add_role_to_farm(**role_params)
