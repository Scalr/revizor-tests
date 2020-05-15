import time
import typing as tp

from selene.elements import SeleneElement
from selene.api import s, ss, by, browser, be, have

from .base import TfBasePage, BasePage

from ui.utils import consts
from ui.utils.components import button, loading_modal, input, search


class RunStep:
    def __init__(self, element: SeleneElement):
        self.element = element

    @property
    def title(self):
        return self.element.s("td.x-title")

    @property
    def status(self):
        return self.element.s("div.x-status")

    def activate(self):
        self.element.click()
        time.sleep(1)


class RunDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(
            be.not_.visible, timeout=20
        )
        s("div.x-grid-buffered-loader-mask").should(be.not_.visible, timeout=10)
        s("[id^=breadcrumbs]").should(have.text("run-"))

    def __init__(self):
        self.element = ss("div.x-abs-layout-item").filtered_by(be.visible)[0]

    @property
    def date(self) -> SeleneElement:
        return self.element.ss("fieldset")[0].ss("div.x-field")[0]

    @property
    def status(self) -> SeleneElement:
        return self.element.ss("fieldset")[0].ss("div.x-field")[1]

    @property
    def run_id(self) -> SeleneElement:
        return self.element.ss("fieldset")[1].ss("div.x-field")[0]

    @property
    def commit(self) -> SeleneElement:
        return self.element.ss("fieldset")[1].ss("div.x-field")[1]

    @property
    def triggered_by(self) -> SeleneElement:
        return self.element.ss("fieldset")[2].ss("div.x-field")[0]

    @property
    def triggered_from(self) -> SeleneElement:
        return self.element.ss("fieldset")[2].ss("div.x-field")[1]

    @property
    def workspace(self) -> SeleneElement:
        return self.element.ss("fieldset")[3].ss("div.x-field")[0]

    @property
    def repository(self) -> SeleneElement:
        return self.element.ss("fieldset")[3].ss("div.x-field")[1]

    @property
    def approve_button(self) -> button:
        return button("Approve", parent=self.element)

    @property
    def decline_button(self) -> button:
        return button("Decline", parent=self.element)

    @property
    def steps(self) -> [RunStep]:
        return [RunStep(e) for e in self.element.ss("div.x-dataview-tab")]

    @property
    def console(self) -> SeleneElement:
        return s("div.x-logviewer-log")

    @property
    def confirm_approve(self) -> button:
        return s(by.xpath("//span[text()='Yes']/ancestor::span"))

    @property
    def confirm_decline(self) -> button:
        return s(by.xpath("//span[text()='Yes']/ancestor::span"))

    @property
    def open_ws_runs(self) -> browser.element:
        return s(by.xpath("//a[text()='Runs']"))


class WorkspaceRunLine:
    def __init__(self, element: browser.element):
        self.element = element

    @property
    def icon_status(self) -> SeleneElement:
        return self.element.ss("td")[0]

    @property
    def date(self) -> SeleneElement:
        return self.element.ss("td")[1].ss("div.x-grid-dataview-cell")[0]

    @property
    def carrent(self) -> SeleneElement:
        return self.element.ss("td")[1].s("span.x-tag-label-blue")

    @property
    def status(self) -> SeleneElement:
        return self.element.ss("td")[1].ss("div.x-grid-dataview-cell")[1]

    @property
    def run_id(self) -> SeleneElement:
        return self.element.ss("td")[2].s("a")[0]

    @property
    def copy_run(self) -> SeleneElement:
        return self.element.ss("td")[2].s("img.x-icon-copy")

    @property
    def commit(self) -> SeleneElement:
        return self.element.ss("td")[2].s("a")[1]

    @property
    def triggered_by(self) -> SeleneElement:
        return self.element.ss("td")[3].ss("div.x-grid-dataview-cell")[0]

    @property
    def triggered_from(self) -> SeleneElement:
        return self.element.ss("td")[3].ss("div.x-grid-dataview-cell")[1]

    @property
    def run_details_button(self) -> button:
        return button(qtip="Run Details", parent=self.element)


class QueueNewRunModal:
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//span[text()='Cancel']/ancestor::span")).should(be.visible)

    @property
    def queue_button(self) -> button:
        return s(by.xpath("//span[text()='Queue Run']/ancestor::span"))

    @property
    def cancel_queue_button(self) -> button:
        return s(by.xpath("//span[text()='Cancel']/ancestor::span"))


class WorkspaceRunsPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal("Loading...").should(be.not_.visible, timeout=10)
        s(by.xpath("//span[text()='Queue run']/ancestor::span")).should(
            be.visible, timeout=20
        )

    @property
    def queue_run(self) -> button:
        return button(title="Queue run")

    @property
    def refresh(self) -> button:
        return s(
            by.xpath(
                "//div[starts-with(@id, 'workspacedashboardruns')]//a[@data-qtip='Refresh']"
            )
        )

    @property
    def workspace_runs(self) -> [WorkspaceRunLine]:
        return [WorkspaceRunLine(p) for p in ss("tr.x-grid-row") if p.is_displayed()]
