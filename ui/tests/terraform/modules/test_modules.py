import typing as tp
import time

import pytest
from selene.api import be, have, query, s, by, ss

from ui.pages.terraform.workspaces import WorkspacePage
from ui.utils import components
from ui.utils import consts


class TestWorkspaceRun:
    workspace_page: WorkspacePage
    name = None
    vcs_provider: tp.Dict[str, str] = None

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.modules_page = tf_dashboard.menu.open_modules()
        self.vcs_provider = vcs_provider

    def get_or_create_module(self, repo_name: str = "Scalr/terraform-aws-rds"):
        module = [
            m
            for m in self.modules_page.modules
            if m.name.get(query.text).strip() == repo_name.split("-")[-1]
        ]
        if module:
            m = module[0]
            m.activate()
            return m
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider["name"])
        new_module.repository.set_value(repo_name)
        new_module.publish_button.click()
        components.loading_modal(consts.LoadingModalMessages.PUBLISH_MODULE).should(
            be.not_.visible, timeout=20
        )
        # self.modules_page.loader.should(be.visible)
        # self.modules_page.loader.should(be._not_.visible, timeout=180)

    def test_add_module(self):
        new_module = self.modules_page.open_new_module()
        init_modules_count = len(self.modules_page.modules)
        new_module.vcs_provider.set_value(self.vcs_provider["name"])
        assert len(new_module.repository.get_values()) > 0
        new_module.repository.set_value("Scalr/terraform-aws-rds")
        new_module.publish_button.click()
        components.loading_modal(consts.LoadingModalMessages.PUBLISH_MODULE).should(
            be.not_.visible, timeout=20
        )
        assert len(self.modules_page.modules) > init_modules_count
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        rds_module = self.modules_page.modules[0]
        assert rds_module.is_syncing()
        assert rds_module.version.should(have._not_.text("SYNCING"), timeout=120)
        assert rds_module.version.get(query.text).strip().replace(".", "").isdigit()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert len(rds_module.description.text.strip()) > 10
        s(by.xpath('//span[text()="Inputs "]/span')).should(have._not_.text('(0)'), timeout=20)
        assert int(s(by.xpath('//span[text()="Inputs "]/span')).get(query.text)[1:-1]) > 0
        assert int(s(by.xpath('//span[text()="Outputs "]/span')).get(query.text)[1:-1]) > 0

    def test_add_module_twice(self):
        repo_name = "Scalr/terraform-aws-rds"
        self.get_or_create_module(repo_name)
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider["name"])
        new_module.repository.set_value(repo_name)
        new_module.publish_button.click()
        components.tooltip('Module "rds" for provider "aws" is already registered').should(
            be.visible
        )

    def test_add_big_module(self):
        init_modules_count = len(self.modules_page.modules)
        self.get_or_create_module("Scalr/terraform-aws-vpc")
        assert len(self.modules_page.modules) > init_modules_count
        vpc_module = self.modules_page.modules[0]
        assert vpc_module.is_syncing()
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert vpc_module.version.should(have._not_.text("SYNCING"), timeout=300)
        assert vpc_module.version.get(query.text).strip().replace(".", "").isdigit()
        assert len(vpc_module.description.text.strip()) > 10

    def test_resync_module(self):
        rds_module = self.get_or_create_module("Scalr/terraform-aws-rds")
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert rds_module.version.should(have._not_.text("SYNCING"), timeout=60)
        assert rds_module.version.get(query.text).strip().replace(".", "").isdigit()
        assert len(rds_module.description.text.strip()) > 10
        rds_module.resync_button.click()
        components.tooltip('Resynchronizing "rds" module successfully started.').should(be.visible)
        rds_module.version.should(have.text("SYNCING"))
        self.modules_page.loader.should(be._not_.visible, timeout=60)
        assert rds_module.version.should(have._not_.text("SYNCING"), timeout=180)
        assert rds_module.version.text.strip().replace(".", "").isdigit()

    def test_remove_module(self):
        rds_module = self.get_or_create_module("Scalr/terraform-aws-rds")
        delete_modal = rds_module.open_delete()
        delete_modal.delete_button.click()
        components.tooltip('Module "rds" successfully deleted.').should(be.visible)
