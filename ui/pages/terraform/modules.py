from selene.api import s, ss, be, have, browser, query
from selene.core.entity import Element

from .base import TfBasePage
from ui.utils import consts
from ui.utils import components


class NewModuleDisplay(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s("//div[contains(@class, 'x-component') and text()='New Module']").should(be.visible)

    @property
    def vcs_provider(self) -> components.combobox:
        return components.combobox("VCS Provider")

    @property
    def repository(self) -> components.combobox:
        return components.combobox("Repository")

    @property
    def publish_button(self) -> components.button:
        return components.button("Publish")

    @property
    def cancel_button(self) -> components.button:
        return components.button("Cancel")


class DeleteModuleModal(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s("div.message").should(have.text("Delete selected Module ")).should(be.visible)

    @property
    def delete_button(self):
        return components.button("Delete", parent=s("div.x-panel-confirm"))

    @property
    def cancel_button(self):
        return components.button("Cancel", parent=s("div.x-panel-confirm"))


class ModuleLine:
    def __init__(self, element: Element):
        self.element = element

    @property
    def name(self) -> Element:
        return self.element.s("strong")

    @property
    def description(self) -> Element:
        return self.element.ss("div.x-grid-cell-inner > div > div")[1].s("div")

    @property
    def version(self) -> Element:
        return self.element.ss("div.x-grid-cell-inner > div > div")[2]

    def activate(self):
        self.element.click()

    def is_syncing(self) -> bool:
        return self.version.get(query.text).strip().lower() == "syncing"

    def is_active(self) -> bool:
        return self.element.matching(have.css_class("x-grid-item-selected"))

    @property
    def resync_button(self) -> components.button:
        return components.button("Resync")

    @property
    def delete_button(self) -> components.button:
        return components.button("Delete")

    def open_delete(self) -> DeleteModuleModal:
        self.delete_button.click()
        return DeleteModuleModal()

    @property
    def versions(self) -> components.combobox:
        return components.combobox("")


class ModulesPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(
            be.not_.visible, timeout=20
        )
        s("div.x-grid-buffered-loader-mask").should(be.not_.visible, timeout=10)
        s("[id^=breadcrumbs]").should(have.text("Modules"))

    @property
    def loader(self) -> Element:
        return s("svg.x-icon-spinner")

    @property
    def search(self) -> components.search:
        return components.search()

    def open_new_module(self) -> NewModuleDisplay:
        components.button("New Module").click()
        return NewModuleDisplay()

    @property
    def reload_button(self) -> components.button:
        return components.button(icon="refresh")

    @property
    def modules(self) -> [ModuleLine]:
        return [ModuleLine(p) for p in ss('table.x-grid-item') if p.is_displayed()]
