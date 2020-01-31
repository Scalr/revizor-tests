import typing as tp

import pytest
from selene.api import be

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage
from ui.utils.components import loading_modal
from ui.utils import consts


class TestVCSProviders:
    workspace_page: WorkspacePage
    vcs_provider: tp.Dict[str, str]
    workspace_name: str
    repo_name: str = 'Scalr/revizor'

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.vcs_provider = vcs_provider
        self.workspace_name = generate_name('name')

    def wait_workspace_save(self):
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.visible, timeout=10)
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.not_.visible, timeout=10)

    def test_create_default_workspace(self):
        workspaces_before = len(self.workspace_page.workspaces)
        modal = self.workspace_page.open_new_workspace()
        modal.name.set(self.workspace_name)
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
        workspace_line = list(filter(lambda x: x.name == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.last_run == '—'
        assert workspace_line.changed_on == '—'
        assert workspace_line.created_by == 'tf@scalr.com'
        assert workspace_line.repository == self.repo_name
        assert workspace_line.launch_button.should(be.visible)

    def test_create_with_auto_apply(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.auto_apply.toggle()
        assert modal.auto_apply.is_checked()
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1

    def test_create_with_branch(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set(self.workspace_name)
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
        workspace_line = list(filter(lambda x: x.name == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1

    def test_create_with_subdirectotry(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.toggle_additional()
        modal.subdirectory.set('subdir')
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name == self.workspace_name, self.workspace_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.repository == f'{self.repo_name} / subdir', f'Subdir not found "{workspace_line.repository}"'

    def test_create_with_work_dir(self):
        modal = self.workspace_page.open_new_workspace()
        modal.name.set(self.workspace_name)
        modal.vcs_provider.set_value(self.vcs_provider['name'])
        modal.repository.set_value(self.repo_name)
        tf_versions = modal.terraform_version.get_values()
        modal.terraform_version.set_value(tf_versions[0])
        modal.toggle_additional()
        modal.work_directory.set('workdir')
        modal.save_button.click()
        self.wait_workspace_save()
        workspace_line = list(filter(lambda x: x.name == self.workspace_name, self.workspace_page.workspaces))
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