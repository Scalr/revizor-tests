import typing as tp
import time

import pytest
from selene.api import by, be, s, ss, query, have

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage
from ui.pages.terraform.runs import WorkspaceRunsPage, QueueNewRunModal, RunDashboard
from ui.utils.components import loading_modal
from ui.utils import consts
from revizor2.api import IMPL


class TestWorkspaceRun:
    workspace_page: WorkspacePage
    name = None
    repo_name: str = "Scalr/tf-revizor-fixtures"
    vcs_provider: str = None

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.vcs_provider = vcs_provider

    def wait_run_queued(self):
        loading_modal(consts.LoadingModalMessages.QUEUEING_RUN).should(be.not_.visible, timeout=5)
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//div[text()='Run successfully queued']")).should(be.visible)

    def wait_runstab_loading(self):
        s(
            by.xpath("//div[starts-with(@id, 'workspacedashboardruns')]//div[text()='Loading...']")
        ).should(be.not_.visible, timeout=20)

    def new_workspace_runs_page(self, subdirectory=None):
        self.workspace_name = generate_name("name")
        self.tf_version = "0.12.19"
        provider_id = self.vcs_provider["id"]
        IMPL.workspace.create(
            self.workspace_name,
            self.tf_version,
            provider=provider_id,
            repository="Scalr/tf-revizor-fixtures",
            branch="master",
            patch=subdirectory,
        )
        time.sleep(1)
        workspace_line = list(
            filter(
                lambda x: x.name.get(query.text).strip() == self.workspace_name,
                self.workspace_page.workspaces,
            )
        )
        assert len(workspace_line) == 1
        self.run_page = workspace_line[0].open_runs_page()
        return self.run_page

    def test_cancel_run(self):
        run_page = self.new_workspace_runs_page("error_plan")
        self.wait_runstab_loading()
        self.run_page.queue_run.click()
        confirm = QueueNewRunModal()
        confirm.cancel_queue_button.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        assert len(self.run_page.workspace_runs) == 0

    def test_error_run(self):
        run_page = self.new_workspace_runs_page("error_plan")
        self.wait_runstab_loading()
        self.run_page.queue_run.click()
        confirm = QueueNewRunModal()
        confirm.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) == 1
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        run_line.status.should(have.text("PLANNING"), timeout=40)
        run_line.status.should(have.text("ERRORED"), timeout=20)
        assert run_line.status.get(query.text) == "ERRORED"
        assert run_line.carrent.get(query.text) == "CURRENT"
        assert run_line.triggered_by.get(query.text) == "tf@scalr.com"
        assert run_line.triggered_from.get(query.text) == " Manual"

    def test_planned_and_finished_run(self):
        run_page = self.new_workspace_runs_page()
        self.wait_runstab_loading()
        self.run_page.queue_run.click()
        confirm = QueueNewRunModal()
        confirm.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) == 1
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.carrent.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"), timeout=40)
        run_line.status.should(have.text("PLANNED AND FINISHED"), timeout=20)
        assert run_line.status.get(query.text) == "PLANNED AND FINISHED"
        assert run_line.triggered_by.get(query.text) == "tf@scalr.com"
        assert run_line.triggered_from.get(query.text) == " Manual"

    def test_approve_run(self):
        run_page = self.new_workspace_runs_page("local_wait")
        self.wait_runstab_loading()
        self.run_page.queue_run.click()
        confirm = QueueNewRunModal()
        confirm.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) > 0
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.carrent.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"))
        run_line.status.should(have.text("NEEDS CONFIRMATION"), timeout=300)
        run_line.run_details_button.click()
        confirm = RunDashboard()
        confirm.approve_button.click()
        confirm.confirm_approve.click()
        confirm.open_ws_runs.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        run_line.status.should(have.text("APPLIED"), timeout=300)
        assert run_line.status.get(query.text) == "APPLIED\n+2 ⇄0–0"

    def test_discared_run(self):
        run_page = self.new_workspace_runs_page("local_wait")
        self.wait_runstab_loading()
        self.run_page.queue_run.click()
        confirm = QueueNewRunModal()
        confirm.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) > 0
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.carrent.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"))
        run_line.status.should(have.text("NEEDS CONFIRMATION"), timeout=300)
        run_line.run_details_button.click()
        confirm = RunDashboard()
        confirm.decline_button.click()
        confirm.confirm_decline.click()
        confirm.open_ws_runs.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.status.get(query.text) == "DISCARDED"
