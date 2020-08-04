import pytest
import time
from selene.api import be, have, query

from ui.pages.terraform.runs import RunDashboard
from ui.utils import consts
from ui.utils.mixins.vcs import VCSMixin
from ui.utils.datagenerator import generate_name
from ui.utils.components import loading_modal, button


class TestTerraformLifecycle(VCSMixin):
    """
    Lifecycle test for terraform.
    1. Create VCS
    2. Create workspace
    3. Start run
    4. Approve run
    5. Wait run applied
    6. Destroy run
    """
    repo_name = 'Scalr/tf-revizor-fixtures'

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, loggined_vcs):
        self.dashboard = tf_dashboard
        self.vcs_provider = loggined_vcs
        self._created_oauth = []
        yield
        for name in self._created_oauth:
            self.vcs_provider.delete_oauth(name)

    def wait_workspace_save(self):  # TODO: Think about waiters
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.visible, timeout=10)
        loading_modal(consts.LoadingModalMessages.SAVING_WORKSPACE).should(be.not_.visible, timeout=10)

    def test_real_success_run(self):
        vcs_name = generate_name('test-')
        workspace_name = generate_name('ws-')
        vcs_page = self.add_provider(vcs_name)
        for provider in vcs_page.providers:
            if provider.name == vcs_name:
                break
        else:
            raise AssertionError(f'VCS Provider with name {vcs_name} not exist in table!')
        ws_page = self.dashboard.menu.open_workspaces()
        form = ws_page.open_new_workspace().open_from_vcs_form()
        form.name.set_value(workspace_name)
        assert len(form.vcs_provider.get_values()) >= 1
        form.vcs_provider.set_value(vcs_name)
        assert len(form.repository.get_values()) >= 1
        form.repository.set_value(self.repo_name)
        form.toggle_additional.click()
        tf_versions = form.terraform_version.get_values()
        assert len(tf_versions) >= 1
        form.terraform_version.set_value('0.12.25')
        form.subdirectory.set('local_wait')
        form.create()
        self.dashboard.menu.open_workspaces()
        assert len(ws_page.workspaces) > 0
        workspace_line = list(filter(lambda x: x.name.get(query.text).strip() == workspace_name, ws_page.workspaces))
        assert len(workspace_line) == 1
        workspace_line = workspace_line[0]
        assert workspace_line.last_run.text.strip() == '—'
        assert workspace_line.changed_on.text.strip() == '—'
        assert workspace_line.created_by.text.strip() == 'tf@scalr.com'
        assert workspace_line.repository.text.strip() == f'{self.repo_name}/local_wait'
        assert workspace_line.launch_button.should(have._not_.css_class('x-grid-action-button-disabled'), timeout=20)  # Wait conf version uploaded
        workspace_line.launch_button.click()
        button('OK').click()
        workspace_line.last_run.should(have.text('NEEDS CONFIRMATION'), timeout=60)
        workspace_line.last_run.s('a').click()
        run_dashboard = RunDashboard()
        run_dashboard.status.should(have.text('NEEDS CONFIRMATION'))
        run_dashboard.approve_button.click()
        button('Yes').should(be.visible).click()
        run_dashboard.status.should(have.text('APPLYING'), timeout=10)
        run_dashboard.status.should(have.text('APPLIED'), timeout=120)
        assert run_dashboard.steps[0].title.text.strip() == '1. Plan'
        assert run_dashboard.steps[0].status.text.strip() == 'Finished'
        run_dashboard.steps[0].activate()
        assert 'Plan: 2 to add, 0 to change, 0 to destroy.' in run_dashboard.console.get(query.text)
        assert 'Traceback' not in run_dashboard.console.get(query.text)
        assert run_dashboard.steps[1].title.text.strip() == '2. Cost estimate'
        assert run_dashboard.steps[1].status.text.strip() == 'Finished'
        run_dashboard.steps[1].activate()
        assert 'Resources: 0 of 0 estimated' in run_dashboard.console.get(query.text)
        assert 'Traceback' not in run_dashboard.console.get(query.text)
        assert run_dashboard.steps[2].title.text.strip() == '3. Policy check'
        assert run_dashboard.steps[2].status.text.strip() == 'Passed'
        assert run_dashboard.steps[3].title.text.strip() == '4. Apply'
        assert run_dashboard.steps[3].status.text.strip() == 'Finished'
        run_dashboard.steps[3].activate()
        assert 'Apply complete! Resources: 2 added, 0 changed, 0 destroyed.' in run_dashboard.console.get(query.text)
        assert 'Traceback' not in run_dashboard.console.get(query.text)
