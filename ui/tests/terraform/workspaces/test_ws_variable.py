import typing as tp
import time

import pytest
from selene.api import by, be, s, query

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage, WorkspaceVariablePage, TFVariableLine
from ui.utils.components import loading_modal
from ui.utils import consts
from revizor2.api import IMPL


class TestWorkspaceVariable:
    workspace_page: WorkspacePage
    ws_variable: WorkspaceVariablePage
    name = None

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.vcs_provider = vcs_provider
        self.workspace_name = generate_name("name")
        self.tf_version = "0.12.19"
        self.var_name = generate_name("name-")
        self.var_value = generate_name("value-")
        IMPL.workspace.create(self.workspace_name, self.tf_version)
        self.workspace_page.reload()
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1
        self.var_dashboard = workspace_line[0].open_variable_dashboard()

    def wait_variable_save(self):
        loading_modal(consts.LoadingModalMessages.SAVING).should(be.visible, timeout=10)
        loading_modal(consts.LoadingModalMessages.SAVING).should(be.not_.visible, timeout=10)
        s(by.xpath("//div[text()='Variables saved']")).should(be.visible)

    def test_variable_page(self):
        assert self.var_dashboard.empty_tf_variable.text == "You have no variables added yet."
        assert len(self.var_dashboard.env_variables) > 0

    def test_create_sensitive_tf_variable(self):
        self.var_dashboard.new_tf_variable.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        variable_line.input_value.set_value(self.var_value)
        variable_line.sensitive_button.click()
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        assert variable_line.input_value.get(query.value) == ""

    def test_create_hcl_tf_variable(self):
        self.var_dashboard.new_tf_variable.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        variable_line.input_value.set_value(self.var_value)
        variable_line.hcl_button.click()
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        assert variable_line.input_value.get(query.value) == self.var_value

    def test_create_tf_variable(self):
        self.var_dashboard.new_tf_variable.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        variable_line.input_value.set_value(self.var_value)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        assert variable_line.input_value.get(query.value) == self.var_value

    def test_update_tf_variable(self):
        self.var_dashboard.new_tf_variable.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        variable_line = self.var_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        variable_line.input_name.set_value("update-tf")
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == "update-tf"

    def test_delete_tf_variable(self):
        self.var_dashboard.new_tf_variable.click()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        variable_line = self.var_dashboard.tf_variables[-1]
        variable_line.delete_button.click()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.tf_variables
        assert len(variable_line) == 0

    def test_create_env_variable(self):
        self.var_dashboard.new_env_variable.click()
        variable_line = self.var_dashboard.env_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        variable_line.input_value.set_value(self.var_value)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        assert variable_line.input_value.get(query.value) == self.var_value

    def test_create_sensitive_env_variable(self):
        self.var_dashboard.new_env_variable.click()
        variable_line = self.var_dashboard.env_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        variable_line.input_value.set_value(self.var_value)
        variable_line.sensitive_button.click()
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        assert variable_line.input_value.get(query.value) == ""

    def test_update_env_variable(self):
        self.var_dashboard.new_env_variable.click()
        variable_line = self.var_dashboard.env_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        variable_line = self.var_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == self.var_name
        variable_line.input_name.set_value("update-env")
        self.var_dashboard.save.click()
        self.wait_variable_save()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == "update-env"

    def test_delete_env_variable(self):
        self.var_dashboard.new_env_variable.click()
        variable_line = self.var_dashboard.env_variables[-1]
        variable_line.input_name.set_value(self.var_name)
        self.var_dashboard.save.click()
        self.wait_variable_save()
        variable_line = self.var_dashboard.env_variables[-1]
        variable_line.delete_button.click()
        self.var_dashboard.refresh.click()
        variable_line = self.var_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) != self.var_name
