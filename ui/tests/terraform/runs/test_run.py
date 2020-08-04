import time
import typing as tp

import pytest
from selene.api import by, be, s, ss, query, have

from ui.utils.datagenerator import generate_name
from ui.pages.terraform.workspaces import WorkspacePage
from ui.pages.terraform.runs import QueueNewRunModal, WorkspaceRunsPage
from ui.utils.components import loading_modal
from ui.utils import consts
from revizor2.api import IMPL


class TestWorkspaceRun:
    workspace_page: WorkspacePage
    name: tp.Optional[str] = None
    repo_name: str = "Scalr/tf-revizor-fixtures"
    tf_version: str = "0.12.25"
    vcs_provider: tp.Dict[str, str] = None

    @pytest.fixture(autouse=True)
    def prepare_env(self, tf_dashboard, vcs_provider):
        self.workspace_page = tf_dashboard.menu.open_workspaces()
        self.vcs_provider = vcs_provider
        self.workspace_name = generate_name("name")
        yield
        ws_id = [w["id"] for w in IMPL.workspace.list() if w["name"] == self.workspace_name]
        if len(ws_id) > 0:
            IMPL.workspace.delete(ws_id[0])

    def wait_run_queued(self):
        loading_modal(consts.LoadingModalMessages.QUEUEING_RUN).should(be.not_.visible, timeout=5)
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//div[text()='Run successfully queued']")).should(be.visible)

    def wait_runstab_loading(self):
        s(
            by.xpath("//div[starts-with(@id, 'workspacedashboardruns')]//div[text()='Loading...']")
        ).should(be.not_.visible, timeout=20)

    def new_workspace_runs_page(self, subdirectory=None) -> WorkspaceRunsPage:
        provider_id = self.vcs_provider["id"]
        IMPL.workspace.create(
            self.workspace_name,
            self.tf_version,
            provider=provider_id,
            repository="Scalr/tf-revizor-fixtures",
            branch="master",
            path=subdirectory,
        )
        self.workspace_page.reload()
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
        modal = self.run_page.open_queue_run()
        modal.cancel_queue_button.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        assert len(self.run_page.workspace_runs) == 0

    def test_error_run(self):
        run_page = self.new_workspace_runs_page("error_plan")
        self.wait_runstab_loading()
        modal = self.run_page.open_queue_run()
        modal.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) == 1
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        run_line.status.should(have.text("PLANNING"), timeout=40)
        run_line.status.should(have.text("ERRORED"), timeout=20)
        assert run_line.status.get(query.text) == "ERRORED"
        assert run_line.current.get(query.text) == "CURRENT"
        assert run_line.triggered_by.get(query.text) == "tf@scalr.com"
        assert run_line.triggered_from.get(query.text) == " Manual"

    def test_planned_and_finished_run(self):
        run_page = self.new_workspace_runs_page()
        self.wait_runstab_loading()
        modal = self.run_page.open_queue_run()
        modal.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) == 1
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.current.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"), timeout=40)
        run_line.status.should(have.text("PLANNED AND FINISHED"), timeout=20)
        assert run_line.status.get(query.text) == "PLANNED AND FINISHED"
        assert run_line.triggered_by.get(query.text) == "tf@scalr.com"
        assert run_line.triggered_from.get(query.text) == " Manual"

    def test_approve_run(self):
        run_page = self.new_workspace_runs_page("local_wait")
        self.wait_runstab_loading()
        modal = self.run_page.open_queue_run()
        modal.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) > 0
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.current.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"))
        run_line.status.should(have.text("NEEDS CONFIRMATION"), timeout=300)
        details = run_line.open_details()
        confirm = details.open_approve()
        confirm.yes_button.click()
        details.open_ws_runs.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        run_line.status.should(have.text("APPLIED"), timeout=300)
        assert run_line.status.get(query.text) == "APPLIED\n+2 ⇄0–0"

    def test_discared_run(self):
        run_page = self.new_workspace_runs_page("local_wait")
        self.wait_runstab_loading()
        modal = self.run_page.open_queue_run()
        modal.queue_button.click()
        self.wait_run_queued()
        assert len(self.run_page.workspace_runs) > 0
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.current.get(query.text) == "CURRENT"
        run_line.status.should(have.text("PLANNING"))
        run_line.status.should(have.text("NEEDS CONFIRMATION"), timeout=300)
        details = run_line.open_details()
        confirm = details.open_decline()
        confirm.yes_button.click()
        details.open_ws_runs.click()
        self.run_page.refresh.click()
        self.wait_runstab_loading()
        run_line = self.run_page.workspace_runs[0]
        assert run_line.status.get(query.text) == "DISCARDED"
