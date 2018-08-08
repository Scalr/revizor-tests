# coding: utf-8
"""
Created on 07.08.18
@author: Eugeny Kurkovich
"""
import pytest
import requests

from api.utils.helpers import uniq_uuid
from api.utils.consts import Platform, BuiltInAutomation


class TestFarms(object):

    os_id = "ubuntu-14-04"

    scope = "environment"

    env_id = "5"

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def create_farm(self, name=None, project_id=None, farm_tpl=None, **kwargs):
        default_project_id = "30c59dba-fc9b-4d0f-83ec-4b5043b12f72"
        default_name = "tmp-api-%s" % uniq_uuid()

        body = dict(
            name=name or default_name,
            project={"id": project_id or default_project_id},
            **kwargs
        )

        resp = self.api.create(
            "/api/v1beta0/user/envId/farms/",
            params=dict(envId=self.env_id),
            body=farm_tpl or body)

        return resp.json_data.data

    def gen_farm_template(self, farm_id):
        tpl = self.api.get(
            "/api/v1beta0/user/envId/farms/farmId/actions/generate-template/",
            params=dict(
                envId=self.env_id,
                farmId=farm_id
            )).json_data.data
        tpl.farm.name = "tmp-api-tpl-%s" % uniq_uuid()
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

    def test_farm_template_base(self):
        # create empty Farm
        farm = self.create_farm()
        # gen tpl from Farm
        farm_tpl = self.gen_farm_template(farm_id=farm.id)
        # create Farm from template
        farm = self.create_farm(
            farm_tpl=farm_tpl.to_dict()
        )
        # check Farm created
        assert farm_tpl.farm.name == self.get_farm(farm_id=farm.id).name
