import typing as tp
import time

import pytest
from selene.api import by, be, s, query

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage, DeleteWorkspaceModal
from ui.utils.components import loading_modal
from ui.utils import consts

# TODO: Add cases
# 1. Start run and check statuses
# 2. approve/decline run and check status
# 3. check success message after start
class TestWorkspaces:
    workspace_page: WorkspacePage
    vcs_provider: tp.Dict[str, str]
    workspace_name: str
    repo_name: str = 'Scalr/tf-revizor-fixtures'

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.vcs_provider = vcs_provider
        self.workspace_name = generate_name('name')

    def wait_workspace_save(self):
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.visible, timeout=10)
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.not_.visible, timeout=10)
        s(by.xpath('//div[text()="New Workspace"]')).should(be.not_.visible)

    # #TODO: Add case when try to add repo without permissions for webhooks
    def test_create_default_workspace(self):
        workspaces_before = len(self.workspace_page.workspaces)
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        assert len(modal.vcs_provider.get_values()) >= 1
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        assert len(modal.repository.get_values()) > 5
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        assert len(tf_versions) >= 1
        modal.terraform_version.set_value(tf_versions[0])
        assert not modal.auto_apply.is_checked()
        modal.save_button.click()
        self.wait_workspace_save()
        assert len(self.workspace_page.workspaces) > workspaces_before
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.last_run.text.strip() == '—'
        assert workspace_line.changed_on.text.strip() == '—'
        assert workspace_line.created_by.text.strip() == 'tf@scalr.com'
        assert workspace_line.repository.text.strip() == self.repo_name
        assert workspace_line.launch_button.should(be.visible)

    def test_create_with_auto_apply(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.auto_apply.toggle()
        assert modal.auto_apply.is_checked()
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1

    def test_create_with_branch(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.toggle_additional()
        branches = modal.branch.get_values()
        assert len(branches) > 1
        modal.branch.set_value(branches[1])
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1

    def test_create_with_subdirectotry(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.toggle_additional()
        modal.subdirectory.set_value('subdir')
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.repository.get(query.text) == f'{self.repo_name}/subdir', f'Subdir not found "{workspace_line.repository}"'

    def test_create_with_work_dir(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.toggle_additional()
        modal.work_directory.set_value('workdir')
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1

    def test_save_without_inputs(self):
        modal = self.workspace_page.open_new_workspace()
        modal.save_button.click()
        assert modal.name.has_error()
        assert modal.name.error == 'This field is required', f'Error is not expected: {modal.name.error}'
        assert modal.vcs_provider.has_error()
        assert modal.vcs_provider.error == 'This field is required', f'Error is not expected: {modal.vcs_provider.error}'
        assert modal.repository.has_error()
        assert modal.repository.error == 'This field is required', f'Error is not expected: {modal.repository.error}'

    def test_search_workspace(self):
        workspace_name = ''
        for i in range(2):
            workspace_name = generate_name('test-')
            modal = self.workspace_page.open_new_workspace()
            modal.name.set_value(workspace_name)
            modal.vcs_provider.set_value(self.vcs_provider['name'])
            modal.repository.set_value(self.repo_name)
            tf_versions = modal.terraform_version.get_values()
            modal.terraform_version.set_value(tf_versions[0])
            modal.save_button.click()
            self.wait_workspace_save()
        self.workspace_page.search.set_value(workspace_name)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.name.get(query.text) == workspace_name

    def test_search_no_found_workspace(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set_value(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.save_button.click()
        self.wait_workspace_save()
        self.workspace_page.search.set_value("qqqqqqqqqqqqqq")
        time.sleep(1)
        assert len(self.workspace_page.workspaces) == 0

    def test_dashboard_workspace(self):
        modal = self.workspace_page.open_new_workspace()
        ws_name = self.workspace_name
        modal.name.set_value(ws_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        dashboard = workspace_line[0].open_dashboard()
        time.sleep(1)
        assert len(dashboard.id.text) > 0
        assert dashboard.name.get(query.text) == ws_name
        assert dashboard.terraform_version.get(query.text) == tf_versions[0]
        assert not dashboard.auto_apply.is_checked()

    def test_delete_workspace(self):
        modal = self.workspace_page.open_new_workspace()
        ws_name = self.workspace_name
        modal.name.set_value(ws_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        dashboard = workspace_line[0].open_dashboard()
        dashboard.delete_button.click()
        confirm = DeleteWorkspaceModal()
        confirm.input_name.set_value(ws_name)
        confirm.visible_button()
        confirm.delete_button.click()
        self.workspace_page.search.set_value(ws_name)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 0

    def test_cancel_delete_workspace(self):
        modal = self.workspace_page.open_new_workspace()
        ws_name = self.workspace_name
        modal.name.set_value(ws_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        dashboard = workspace_line[0].open_dashboard()
        dashboard.delete_button.click()
        confirm = DeleteWorkspaceModal()
        confirm.input_name.set_value(ws_name)
        confirm.cancel_delete_button.click()
        dashboard.menu.open_workspaces()
        self.workspace_page.search.set_value(ws_name)
        time.sleep(1)
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
