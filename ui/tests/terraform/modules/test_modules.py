import typing as tp

import pytest
from selene.api import be, have

from ui.pages.terraform.workspaces import WorkspacePage
from ui.utils import components


class TestWorkspaceRun:
    workspace_page: WorkspacePage
    name = None
    repo_name: str = "Scalr/tf-revizor-fixtures"
    vcs_provider: tp.Dict[str, str] = None

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.modules_page = tf_dashboard.menu.open_modules()
        self.vcs_provider = vcs_provider

    def create_module(self, repo_name):
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider['name'])
        new_module.repository.set_value("Scalr/terraform-aws-rds")
        new_module.publish_button.click()
        self.modules_page.loader.should(be.visible)

    def test_add_module(self):
        new_module = self.modules_page.open_new_module()
        init_modules_count = len(self.modules_page.modules)
        new_module.vcs_provider.set_value(self.vcs_provider['name'])
        assert len(new_module.repository.get_values()) > 0
        new_module.repository.set_value("Scalr/terraform-aws-rds")
        new_module.publish_button.click()
        self.modules_page.loader.should(be.visible)
        assert len(self.modules_page.modules) > init_modules_count
        rds_module = self.modules_page.modules[0]
        assert rds_module.is_syncing()
        assert rds_module.is_active()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert rds_module.version.should(have._not_.text("Syncing"), timeout=60)
        assert rds_module.version.text.strip().replace('.', '').isdigit()
        assert len(rds_module.description.text.strip()) > 10

    def test_add_module_twice(self):
        repo_name = "Scalr/terraform-aws-rds"
        self.create_module(repo_name)
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider['name'])
        new_module.repository.set_value(repo_name)
        new_module.publish_button.click()
        components.tooltip('Module "rds" for provider "aws" is already registered').should(be.visible)

    def test_add_big_module(self):
        init_modules_count = len(self.modules_page.modules)
        self.create_module("Scalr/terraform-aws-vpc")
        assert len(self.modules_page.modules) > init_modules_count
        vpc_module = self.modules_page.modules[0]
        assert vpc_module.is_syncing()
        assert vpc_module.is_active()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert vpc_module.version.should(have._not_.text("Syncing"), timeout=60)
        assert vpc_module.version.text.strip().replace('.', '').isdigit()
        assert len(vpc_module.description.text.strip()) > 10

    def test_resync_module(self):
        self.create_module("Scalr/terraform-aws-rds")
        rds_module = self.modules_page.modules[0]
        assert rds_module.is_syncing()
        assert rds_module.is_active()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert rds_module.version.should(have._not_.text("Syncing"), timeout=60)
        assert rds_module.version.text.strip().replace('.', '').isdigit()
        assert len(rds_module.description.text.strip()) > 10
        rds_module.resync_button.click()
        self.modules_page.loader.should(be.visible)
        assert rds_module.is_syncing()
        assert rds_module.is_active()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert rds_module.version.should(have._not_.text("Syncing"), timeout=60)
        assert rds_module.version.text.strip().replace('.', '').isdigit()

    def test_remove_module(self):
        self.create_module("Scalr/terraform-aws-rds")
        rds_module = self.modules_page.modules[0]
        delete_modal = rds_module.open_delete()
        delete_modal.delete_button.click()
        components.tooltip('Module "rds" successfully deleted.').should(be.visible)
