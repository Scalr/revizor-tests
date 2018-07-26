# coding: utf-8
"""
Created on 13.06.18
@author: Eugeny Kurkovich
"""

import pytest

from api.utils.helpers import Platform, uniq_uuid


class TestNewRoles(object):

    os_id = "ubuntu-14-04"

    scope = "environment"

    env_id = "5"

    dev_role_category = 9

    cloud_platforms = [
        Platform.EC2,
        Platform.GCE,
        Platform.CLOUDSTACK]

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def create_role(self, os_id, role_category):
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/",
            params=dict(envId=self.env_id),
            body=dict(
                builtinAutomation=["base"],
                category={"id": role_category},
                name="tmp-api-%s" % uniq_uuid(),
                os={"id": os_id}))
        return resp.json_data.data

    def create_role_image(self, role_id, image_id):
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/roleId/images/",
            params=dict(
                envId=self.env_id,
                roleId=role_id),
            body=dict(
                image={'id': image_id},
                role={'id': role_id}
            ))
        return resp.json_data.data

    def list_images(self, platform=None, os=None, scope=None, agent_installed=True):
        resp = self.api.list(
            "/api/v1beta0/user/envId/images/",
            params=dict(envId=self.env_id),
            filters=dict(
                cloudPlatform=platform,
                os=os,
                scalrAgentInstalled=agent_installed,
                scope=scope
            )
        )
        return resp.json_data.data

    def list_role_images(self, role_id, image=None, role=None):
        resp = self.api.list(
            "/api/v1beta0/user/envId/roles/roleId/images/",
            params=dict(
                envId=self.env_id,
                roleId=role_id),
            filters=dict(
                image=image,
                role=role)
        )
        return resp.json_data.data

    def test_new_role_one_existing_image(self):
        # Create new role
        role = self.create_role(
            self.os_id,
            self.dev_role_category)
        # Find image
        images = list(filter(
            lambda i:
                i.cloudFeatures.virtualization == "hvm" and
                i.name.startswith("mbeh1") and
                i.status == 'active',
            self.list_images(
                    platform=Platform.EC2,
                    os=self.os_id,
                    scope=self.scope)))
        assert images, "images with given search criteria not found"
        image_id = images[0].id
        # Add image to role
        self.create_role_image(role.id, image_id)
        # Assert role images
        assert list(filter(
            lambda i:
                image_id == i.image.id,
            self.list_role_images(role.id)))

    def test_new_role_existing_images(self):
        images = list()
        image_name_suffix = "mbeh1"

        # Create new role
        role = self.create_role(
            self.os_id,
            self.dev_role_category)
        # Get images
        for platform in self.cloud_platforms:
            platform_images = list(filter(
                lambda i:
                    i.name.startswith(image_name_suffix) and
                    i.status == 'active',
                self.list_images(
                        platform=platform,
                        os=self.os_id,
                        scope=self.scope)))
            assert platform_images, "images with given search criteria " \
                                    "{platform}:{pattern}* not found".format(
                                        platform=platform,
                                        pattern=image_name_suffix)
            images.append(platform_images[0].id)
        # Add images to role
        for image_id in images:
            self.create_role_image(role.id, image_id)
        # Assert role images
        assert all(ri.image.id in images for ri in self.list_role_images(role.id))

