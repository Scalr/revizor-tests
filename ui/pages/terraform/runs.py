import time
import typing as tp

from selene.core.entity import Element
from selene.api import s, ss, by, browser, be, have

from .base import TfBasePage

from ui.utils import consts
from ui.utils import components


class RunStep:
    def __init__(self, element: Element):
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


class ConfirmModalMixin:
    @property
    def yes_button(self) -> components.button:
        return components.button("Yes")

    @property
    def no_button(self) -> components.button:
        return components.button("No")


class ApproveRunModal(TfBasePage, ConfirmModalMixin):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="Are you sure you want to approve run?"]')).with_(timeout=20).should(be.visible)


class DeclineRunModal(TfBasePage, ConfirmModalMixin):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="Are you sure you want to decline run?"]')).with_(timeout=20).should(be.visible)


class RunDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible, timeout=20)
        s("div.x-grid-buffered-loader-mask").should(be.not_.visible, timeout=10)
        s("[id^=breadcrumbs]").should(have.text("run-"))

    def __init__(self):
        self.element = ss("div.x-abs-layout-item").filtered_by(be.visible)[0]

    @property
    def date(self) -> Element:
        return self.element.ss("fieldset")[0].ss("div.x-field")[0]

    @property
    def status(self) -> Element:
        return self.element.ss("fieldset")[0].ss("div.x-field")[1]

    @property
    def run_id(self) -> Element:
        return self.element.ss("fieldset")[1].ss("div.x-field")[0]

    @property
    def commit(self) -> Element:
        return self.element.ss("fieldset")[1].ss("div.x-field")[1]

    @property
    def triggered_by(self) -> Element:
        return self.element.ss("fieldset")[2].ss("div.x-field")[0]

    @property
    def triggered_from(self) -> Element:
        return self.element.ss("fieldset")[2].ss("div.x-field")[1]

    @property
    def workspace(self) -> Element:
        return self.element.ss("fieldset")[3].ss("div.x-field")[0]

    @property
    def repository(self) -> Element:
        return self.element.ss("fieldset")[3].ss("div.x-field")[1]

    @property
    def approve_button(self) -> components.button:
        return components.button("Approve", parent=self.element)

    @property
    def decline_button(self) -> components.button:
        return components.button("Decline", parent=self.element)

    @property
    def steps(self) -> [RunStep]:
        return [RunStep(e) for e in self.element.ss("div.x-dataview-tab")]

    @property
    def console(self) -> Element:
        return s("div.x-logviewer-log")

    @property
    def open_ws_runs(self) -> browser.element:
        return s(by.xpath("//a[text()='Runs']"))

    def open_approve(self) -> ApproveRunModal:
        self.approve_button.click()
        return ApproveRunModal()

    def open_decline(self) -> DeclineRunModal:
        self.decline_button.click()
        return DeclineRunModal()


class WorkspaceRunLine:
    def __init__(self, element: browser.element):
        self.element = element

    @property
    def icon_status(self) -> Element:
        return self.element.ss("td")[0]

    @property
    def date(self) -> Element:
        return self.element.ss("td")[1].ss("div.x-grid-dataview-cell")[0]

    @property
    def current(self) -> Element:
        return self.element.ss("td")[1].s("span.x-tag-label-blue")

    @property
    def status(self) -> Element:
        return self.element.ss("td")[1].ss("div.x-grid-dataview-cell")[1]

    @property
    def run_id(self) -> Element:
        return self.element.ss("td")[2].s("a")[0]

    @property
    def copy_run(self) -> Element:
        return self.element.ss("td")[2].s("img.x-icon-copy")

    @property
    def commit(self) -> Element:
        return self.element.ss("td")[2].s("a")[1]

    @property
    def triggered_by(self) -> Element:
        return self.element.ss("td")[3].ss("div.x-grid-dataview-cell")[0]

    @property
    def triggered_from(self) -> Element:
        return self.element.ss("td")[3].ss("div.x-grid-dataview-cell")[1]

    @property
    def run_details_button(self) -> components.button:
        return components.button(qtip="Run Details", parent=self.element)

    def open_details(self) -> RunDashboard:
        self.run_details_button.click()
        return RunDashboard()


class QueueNewRunModal:
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//span[text()='Cancel']/ancestor::span")).should(be.visible, timeout=10)

    @property
    def queue_button(self) -> components.button:
        return components.button("OK")

    @property
    def cancel_queue_button(self) -> components.button:
        return components.button("Cancel")


class WorkspaceRunsPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_page.should(be.not_.visible, timeout=10)
        s(by.xpath("//span[text()='Queue run']/ancestor::a")).should(be.visible, timeout=20)

    @property
    def queue_run_button(self) -> components.button:
        return components.button(title="Queue run")

    @property
    def refresh(self) -> Element:
        return s(
            by.xpath("//div[starts-with(@id, 'workspacedashboardruns')]//a[@data-qtip='Refresh']")
        )

    @property
    def workspace_runs(self) -> [WorkspaceRunLine]:
        return [WorkspaceRunLine(p) for p in ss("tr.x-grid-row") if p.is_displayed()]

    def open_queue_run(self) -> QueueNewRunModal:
        self.queue_run_button.click()
        return QueueNewRunModal()
