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
        self.workspace_name = generate_name('name')
        self.tf_versions = "0.12.19"
        self.var_name = generate_name('name-')
        self.var_value = generate_name('value-')

    def wait_variable_save(self):
        loading_modal(consts.LoadingModalMessages.SAVING).should(be.visible, timeout=10)
        loading_modal(consts.LoadingModalMessages.SAVING).should(be.not_.visible, timeout=10)
        s(by.xpath("//div[text()='Variables saved']")).should(be.visible)
    

    def test_variable_page(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        dashboard = workspace_line[0].open_variable_dashboard()
        assert dashboard.empty_tf_variable.text == "You have no variables added yet."
        assert len(dashboard.env_variables) > 0
        
    def test_create_sensitive_tf_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        var_value = self.var_value
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_tf_variable.click()
        variable_line = variable_dashboard.tf_variables[-1]
        time.sleep(1)
        variable_line.input_name.set_value(var_name)
        variable_line.input_value.set_value(var_value)
        variable_line.sensitive_button.click()
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == var_name
        assert variable_line.input_value.get(query.value) == ''
        
    def test_create_hct_tf_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        var_value = self.var_value
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_tf_variable.click()
        variable_line = variable_dashboard.tf_variables[-1]
        time.sleep(1)
        variable_line.input_name.set_value(var_name)
        variable_line.input_value.set_value(var_value)
        variable_line.hcl_button.click()
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == var_name
        assert variable_line.input_value.get(query.value) == var_value

    def test_create_tf_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        var_value = self.var_value
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_tf_variable.click()
        variable_line = variable_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(var_name)
        variable_line.input_value.set_value(var_value)
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.tf_variables[-1]
        assert variable_line.input_name.get(query.value) == var_name
        assert variable_line.input_value.get(query.value) == var_value

    def test_delete_tf_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_tf_variable.click()
        variable_line = variable_dashboard.tf_variables[-1]
        variable_line.input_name.set_value(var_name)
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.tf_variables[-1]
        variable_line.delete_button.click()
        time.sleep(1)
        variable_line = variable_dashboard.tf_variables
        assert len(variable_line) == 0
        
    def test_create_env_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        var_value = self.var_value
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_env_variable.click()
        variable_line = variable_dashboard.env_variables[-1]
        variable_line.input_name.set_value(var_name)
        variable_line.input_value.set_value(var_value)
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == var_name
        assert variable_line.input_value.get(query.value) == var_value

    def test_create_sensitive_env_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        var_value = self.var_value
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_env_variable.click()
        variable_line = variable_dashboard.env_variables[-1]
        variable_line.input_name.set_value(var_name)
        variable_line.input_value.set_value(var_value)
        variable_line.sensitive_button.click()
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) == var_name
        assert variable_line.input_value.get(query.value) == ''

    def test_delete_env_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        var_name = self.var_name
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        variable_dashboard.new_env_variable.click()
        variable_line = variable_dashboard.env_variables[-1]
        variable_line.input_name.set_value(var_name)
        variable_dashboard.save.click()
        self.wait_variable_save()
        variable_line = variable_dashboard.env_variables[-1]
        variable_line.delete_button.click()
        variable_line = variable_dashboard.env_variables[-1]
        assert variable_line.input_name.get(query.value) != var_name



    #  тот что не работает (оставила не всякий случай)
    def test_search_tf_variable(self):
        ws_name = self.workspace_name
        tf_versions = self.tf_versions
        IMPL.workspace.create(ws_name, tf_versions)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == ws_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        variable_dashboard = workspace_line[0].open_variable_dashboard()
        for i in range(2):
            var_name = generate_name('test-')
            variable_dashboard.new_tf_variable.click()
            variable_line = variable_dashboard.tf_variables[-1]
            variable_line.input_name.set_value(var_name)
            time.sleep(1)
        variable_dashboard.save.click()
        self.wait_variable_save()
        time.sleep(2)
        variable_dashboard.search.set_value("var_name")
        time.sleep(1)
        variable_line = variable_dashboard.tf_variables[-1]
        assert len(variable_line) == 1
        variable_line.input_name.get(query.value) == var_name
