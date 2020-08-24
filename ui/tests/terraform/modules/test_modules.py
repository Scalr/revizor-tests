import typing as tp
import time

import pytest
from selene.api import be, have, query, s
from revizor2.api import IMPL

from ui.pages.terraform.modules import ModulesPage
from ui.utils import components


class TestModules:
    modules_page: ModulesPage
    name = None
    vcs_provider: tp.Dict[str, str] = None

    @pytest.fixture(scope="class", autouse=True)
    def remove_all_modules(self):
        for m in IMPL.modules.list():
            IMPL.modules.delete(m["id"], m["name"])

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.modules_page = tf_dashboard.menu.open_modules()
        self.vcs_provider = vcs_provider

    def get_or_create_module(self, repo_name: str = "Scalr/terraform-aws-rds"):
        def get_module(repo_name: str):
            module = [
                m
                for m in self.modules_page.modules
                if m.name.get(query.text).strip() == repo_name.split("-")[-1]
            ]
            if module:
                return module[0]

        m = get_module(repo_name)
        if m:
            return m
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider["name"])
        new_module.repository.set_value(repo_name)
        dashboard = new_module.create()
        dashboard.menu.open_modules()
        return get_module(repo_name)

    def test_add_module(self):
        init_modules_count = len(self.modules_page.modules)
        new_module = self.modules_page.open_new_module()
        new_module.vcs_provider.set_value(self.vcs_provider["name"])
        assert len(new_module.repository.get_values()) > 0
        new_module.repository.set_value("Scalr/terraform-aws-rds")
        dashboard = new_module.create()
        dashboard.menu.open_modules()
        assert len(self.modules_page.modules) > init_modules_count
        rds_module = self.modules_page.modules[0]
        assert rds_module.is_syncing()
        assert rds_module.version.should(have.no.text("SYNCING"), timeout=120)
        assert rds_module.version.get(query.text).strip().replace(".", "").isdigit()
        assert len(rds_module.description.text.strip()) > 10
        # s(by.xpath('//span[text()="Inputs "]/span')).should(have.no.text('(0)'), timeout=20)
        # assert int(s(by.xpath('//span[text()="Inputs "]/span')).get(query.text)[1:-1]) > 0
        # assert int(s(by.xpath('//span[text()="Outputs "]/span')).get(query.text)[1:-1]) > 0

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
        assert vpc_module.version.should(have.no.text("SYNCING"), timeout=300)
        assert vpc_module.version.get(query.text).strip().replace(".", "").isdigit()
        assert len(vpc_module.description.text.strip()) > 10

    def test_resync_module(self):
        rds_module = self.get_or_create_module("Scalr/terraform-aws-rds")
        assert rds_module.version.with_(timeout=180).should(have.no.text("SYNCING"))
        version = rds_module.version.get(query.text)
        assert version.strip().replace(".", "").isdigit(), f"Version is not digit: {version}"
        assert len(rds_module.description.text.strip()) > 10
        dashboard = rds_module.open_dashboard()
        dashboard.resync_button.click()
        components.tooltip('Resynchronizing "rds" module successfully started.').should(be.visible)
        dashboard.menu.open_modules()
        time.sleep(0.5)
        self.modules_page.reload_button.click()
        s("div.x-grid-buffered-loader").should(be.not_.visible, timeout=10)
        time.sleep(1)
        rds_module = self.get_or_create_module("Scalr/terraform-aws-rds")
        rds_module.version.should(have.text("SYNCING"))
        assert rds_module.version.should(have.no.text("SYNCING"), timeout=180)
        version = rds_module.version.get(query.text)
        assert version.strip().replace(".", "").isdigit(), f"Version is not digit: {version}"

    def test_remove_module(self):
        rds_module = self.get_or_create_module("Scalr/terraform-aws-rds")
        dashboard = rds_module.open_dashboard()
        delete_modal = dashboard.open_delete_module()
        delete_modal.delete_button.click()
        components.tooltip('Module "rds" successfully deleted.').should(be.visible)
