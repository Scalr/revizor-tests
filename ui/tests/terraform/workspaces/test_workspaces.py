import typing as tp
import time

import pytest
from selene.api import by, be, s, ss, query, have
from revizor2.api import IMPL

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage, DeleteWorkspaceModal

# TODO: Add cases
# 1. Start run and check statuses
# 2. approve/decline run and check status
# 3. check success message after start
class TestWorkspaces:
    workspace_page: WorkspacePage
    vcs_provider: tp.Dict[str, str]
    workspace_name: str
    repo_name: str = "Scalr/tf-revizor-fixtures"

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.vcs_provider = vcs_provider
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.workspace_name = generate_name("name")
        yield
        ws_id = [w["id"] for w in IMPL.workspace.list() if w["name"] == self.workspace_name]
        if len(ws_id) > 0:
            IMPL.workspace.delete(ws_id[0])

    # TODO: Add case when try to add repo without permissions for webhooks
    def test_create_default_workspace(self):
        workspaces_before = len(self.workspace_page.workspaces)
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(self.workspace_name)
        assert len(form.vcs_provider.get_values()) >= 1
        form.vcs_provider.set_value(self.vcs_provider["name"])
        assert len(form.repository.get_values()) >= 1
        form.repository.set_value(self.repo_name)
        form.create()
        self.workspace_page.menu.open_workspaces()
        assert len(self.workspace_page.workspaces) > workspaces_before
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.last_run.text.strip() == "—"
        assert workspace_line.changed_on.text.strip() == "—"
        assert workspace_line.created_by.text.strip() == "tf@scalr.com"
        assert workspace_line.repository.text.strip() == self.repo_name
        assert workspace_line.launch_button.should(be.visible)

    def test_create_with_auto_apply(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(self.workspace_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        form.toggle_additional().click()
        form.auto_apply.toggle()
        assert form.auto_apply.is_checked()
        dashboard = form.create()
        assert dashboard.auto_apply.is_checked()
        self.workspace_page.menu.open_workspaces()
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1

    def test_create_with_branch(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(self.workspace_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        form.toggle_additional().click()
        branches = form.branch.get_values()
        assert len(branches) > 1
        form.branch.set_value(branches[1])
        form.create()
        self.workspace_page.menu.open_workspaces()
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1

    def test_create_with_subdirectotry(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(self.workspace_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        form.toggle_additional().click()
        form.subdirectory.set_value("subdir")
        dashboard = form.create()
        assert dashboard.subdirectory.get(query.text).strip() == "subdir"
        self.workspace_page.menu.open_workspaces()
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert (
            workspace_line.repository.get(query.text) == f"{self.repo_name}/subdir"
        ), f'Subdir not found "{workspace_line.repository}"'

    def test_create_with_work_dir(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(self.workspace_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        form.toggle_additional().click()
        form.work_directory.set_value("workdir")
        form.create()
        self.workspace_page.menu.open_workspaces()
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1

    def test_input_errors(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value("a")
        form.name.clear()
        form.create_button.is_disabled()
        assert form.name.has_error()
        assert (
            form.name.error == "This field is required"
        ), f"Error is not expected: {form.name.error}"

    def test_search_workspace(self):
        workspace_name = ""
        for i in range(2):
            workspace_name = generate_name("test-")
            form = self.workspace_page.open_new_workspace().open_from_vcs_form()
            form.name.set_value(workspace_name)
            form.vcs_provider.set_value(self.vcs_provider["name"])
            form.repository.set_value(self.repo_name)
            form.create()
            self.workspace_page.menu.open_workspaces()
        self.workspace_page.search.set_value(workspace_name)
        time.sleep(1)
        assert len(self.workspace_page.workspaces) == 1
        workspace_line = self.workspace_page.workspaces[0]
        assert workspace_line.name.get(query.text) == workspace_name

    def test_search_no_found_workspace(self):
        self.workspace_page.menu.open_workspaces()
        self.workspace_page.search.set_value("qqqqqqqqqqqqqq")
        self.workspace_page.empty_ws_table.should(have.text("No Workspaces found."), timeout=10)
        assert len(self.workspace_page.workspaces) == 0

    def test_workspace_dashboard(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        ws_name = self.workspace_name
        form.name.set_value(ws_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        form.toggle_additional().click()
        time.sleep(0.5)
        tf_versions = form.terraform_version.get_values()
        dashboard = form.create()
        assert dashboard.id.get(query.text).startswith("ws")
        assert dashboard.name.get(query.text) == ws_name
        assert dashboard.terraform_version.get(query.text) == tf_versions[0]
        assert not dashboard.auto_apply.is_checked()

    def test_delete_workspace(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        ws_name = self.workspace_name
        form.name.set_value(ws_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        dashboard = form.create()
        dashboard.delete_button.click()
        confirm = DeleteWorkspaceModal()
        confirm.input_name.set_value(ws_name)
        confirm.delete_button.click()
        self.workspace_page.search.set_value(ws_name)
        self.workspace_page.empty_ws_table.should(have.text("No Workspaces found."), timeout=10)
        assert len(self.workspace_page.workspaces) == 0

    def test_cancel_delete_workspace(self):
        form = self.workspace_page.open_new_workspace().open_from_vcs_form()
        ws_name = self.workspace_name
        form.name.set_value(ws_name)
        form.vcs_provider.set_value(self.vcs_provider["name"])
        form.repository.set_value(self.repo_name)
        dashboard = form.create()
        dashboard.delete_button.click()
        confirm = DeleteWorkspaceModal()
        confirm.input_name.set_value(ws_name)
        confirm.cancel_button.click()
        dashboard.menu.open_workspaces()
        self.workspace_page.search.set_value(ws_name)
        time.sleep(1)
        assert len(self.workspace_page.workspaces) == 1
