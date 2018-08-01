# coding: utf-8
"""
Created on 13.06.18
@author: Eugeny Kurkovich
"""

import pytest
import requests
import six

from api.utils.helpers import Platform, BuiltInAutomation, uniq_uuid


class TestNewRoles(object):

    os_id = "ubuntu-14-04"

    scope = "environment"

    env_id = "5"

    dev_role_category = 9

    @pytest.fixture(autouse=True)
    def init_session(self, api):
        self.api = api

    def create_role(self, os_id, role_category, automation=None):
        builtin_automation = automation or BuiltInAutomation.BASE
        if isinstance(builtin_automation, six.string_types):
            builtin_automation = [builtin_automation]
        resp = self.api.create(
            "/api/v1beta0/user/envId/roles/",
            params=dict(envId=self.env_id),
            body=dict(
                builtinAutomation=builtin_automation,
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
        assert images
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

        cloud_platforms = [
            Platform.EC2,
            Platform.GCE,
            Platform.CLOUDSTACK]

        # Create new role
        role = self.create_role(
            self.os_id,
            self.dev_role_category)
        # Get images
        for platform in cloud_platforms:
            platform_images = list(filter(
                lambda i:
                    i.name.startswith("mbeh1") and
                    i.status == 'active',
                self.list_images(
                        platform=platform,
                        os=self.os_id,
                        scope=self.scope)))
            assert platform_images
            images.append(platform_images[0].id)
        # Add images to role
        for image_id in images:
            self.create_role_image(role.id, image_id)
        # Assert role images
        assert all(ri.image.id in images for ri in self.list_role_images(role.id))

    def test_new_role_invalid_os_id(self):
        invalid_os_id = "ubuntu-19-04"
        exc_message = "'Role.os.id' ({}) was not found.".format(
            invalid_os_id)
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_role(
                invalid_os_id,
                self.dev_role_category)
        assert exc_message in e.value.args[0]

    def test_new_role_invalid_automation_types(self):
        exc_message = "'Role.builtinAutomation' ({}) " \
                      "are invalid".format(
                        BuiltInAutomation.INVALID)
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_role(
                self.os_id,
                self.dev_role_category,
                automation=BuiltInAutomation.INVALID)
        assert exc_message in e.value.args[0]

    def test_new_role_uncombined_behaviors(self):
        exc_message = "'Role.builtinAutomation' ({}, {}) " \
                      "behaviors can't be combined.".format(
                        *BuiltInAutomation.UNCOMBINED_BEHAVIORS)
        with pytest.raises(requests.exceptions.HTTPError) as e:
            self.create_role(
                self.os_id,
                self.dev_role_category,
                automation=BuiltInAutomation.UNCOMBINED_BEHAVIORS)
        assert exc_message in e.value.args[0]

    def test_new_role_one_platform_two_images(self):
        # Find images
        images = list(filter(
            lambda i:
                i.cloudFeatures.virtualization == "hvm" and
                i.name.startswith("mbeh") and
                i.status == 'active',
            self.list_images(
                    platform=Platform.EC2,
                    os=self.os_id,
                    scope=self.scope)))
        assert images
        # Create new role
        role = self.create_role(
            self.os_id,
            self.dev_role_category)
        # Add images to role
        with pytest.raises(requests.exceptions.HTTPError) as e:
            for image in images:
                exc_message = "'RoleImage.image.id' ({}) with 'cloudLocation' " \
                              "({}) has already been registered.".format(
                                image.cloudImageId,
                                image.cloudLocation)
                self.create_role_image(role.id, image.id)
        assert exc_message in e.value.args[0]
