import time
import typing as tp

from selene.elements import SeleneElement
from selene.api import s, ss, by, browser, be, have

from .base import TfBasePage

from ui.utils import consts
from ui.utils.components import loading_modal
from ui.utils.components import button, combobox, toggle, loading_modal, input, search


class RunStep:
    def __init__(self, element: SeleneElement):
        self.element = element

    @property
    def title(self):
        return self.element.s('td.x-title')

    @property
    def status(self):
        return self.element.s('div.x-status')

    def activate(self):
        self.element.click()
        time.sleep(1)


class RunDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible, timeout=20)
        s('div.x-grid-buffered-loader-mask').should(be.not_.visible, timeout=10)
        s('[id^=breadcrumbs]').should(have.text('run-'))

    def __init__(self):
        self.element = ss('div.x-abs-layout-item').filtered_by(be.visible)[0]

    @property
    def date(self) -> SeleneElement:
        return self.element.ss('fieldset')[0].ss('div.x-field')[0]

    @property
    def status(self) -> SeleneElement:
        return self.element.ss('fieldset')[0].ss('div.x-field')[1]

    @property
    def run_id(self) -> SeleneElement:
        return self.element.ss('fieldset')[1].ss('div.x-field')[0]

    @property
    def commit(self) -> SeleneElement:
        return self.element.ss('fieldset')[1].ss('div.x-field')[1]

    @property
    def triggered_by(self) -> SeleneElement:
        return self.element.ss('fieldset')[2].ss('div.x-field')[0]

    @property
    def triggered_from(self) -> SeleneElement:
        return self.element.ss('fieldset')[2].ss('div.x-field')[1]

    @property
    def workspace(self) -> SeleneElement:
        return self.element.ss('fieldset')[3].ss('div.x-field')[0]

    @property
    def repository(self) -> SeleneElement:
        return self.element.ss('fieldset')[3].ss('div.x-field')[1]

    @property
    def approve_button(self) -> button:
        return button('Approve', parent=self.element)

    @property
    def decline_button(self) -> button:
        return button('Decline', parent=self.element)

    @property
    def steps(self) -> [RunStep]:
        return [RunStep(e) for e in self.element.ss('div.x-dataview-tab')]

    @property
    def console(self) -> SeleneElement:
        return s('div.x-logviewer-log')
