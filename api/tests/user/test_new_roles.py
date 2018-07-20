# coding: utf-8
"""
Created on 13.06.18
@author: Eugeny Kurkovich
"""

import pytest

from api.utils.helpers import uniq_uuid

app_level = "user"


class TestNewRoles(object):

    os_id = "ubuntu-14-04"
    scope = "environment"
    env_id = "5"
    platform = "ec2"
    dev_role_category = 9

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def list_images(self, platform=None, os=None, scope=None):
        resp = self.api.list(
            "/api/v1beta0/user/envId/images/",
            params=dict(envId=self.env_id),
            filters=dict(
                cloudPlatform=platform,
                os=os,
                scalrAgentInstalled=True,
                scope=scope
            )
        )
        assert resp.ok
        return resp.json().get('data')

    def test_new_role_one_existing_image(self):
        # Create new role
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/",
            params=dict(envId=self.env_id),
            body=dict(
                builtinAutomation=["base"],
                category={"id": self.dev_role_category},
                name="tmp-api-%s" % uniq_uuid(),
                os={"id": self.os_id}))
        assert resp.status_code == 201
        role = resp.json()['data']
        # Find image
        images = list(filter(
            lambda i:
                i['cloudFeatures']['virtualization'] == "hvm" and
                i['name'].startswith("mbeh1") and
                i['status'] == 'active',
            self.list_images(
                    platform=self.platform,
                    os=self.os_id,
                    scope=self.scope)))
        assert images, "images with given search criteria not found"
        # Add image to role
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/roleId/images/",
            params=dict(
                envId=self.env_id,
                roleId=role['id']),
            body=dict(
                image={'id': images[0]['id']},
                role={'id': role['id']}
            ))
        assert resp.status_code == 201

