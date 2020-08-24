from selene.api import s, ss, by, be, have, query
from selene.core.entity import Element

from .base import TfBasePage
from ui.utils import consts
from ui.utils import components


class CreateModulePage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        ss(by.xpath("//div[text()='New Module']")).element_by(be.visible).with_(timeout=10).should(be.visible)

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

    def create(self) -> "ModuleDashboard":
        self.publish_button.click()
        return ModuleDashboard()


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


class ModuleDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.PUBLISH_MODULE).with_(timeout=30).should(
            be.not_.visible
        )
        components.loading_page.with_(timeout=180).should(be.not_.visible)

    @property
    def delete_button(self) -> components.button:
        return components.button("Delete")

    @property
    def resync_button(self) -> components.button:
        return components.button("Resync")

    def open_delete_module(self) -> DeleteModuleModal:
        self.delete_button.click()
        return DeleteModuleModal()

    def get_instruction_text(self) -> str:
        s("//div[text()='Instructions']").click()
        s("//div[text()='Copy and paste this into your Terraform template and set variable values if needed:']").should(be.visible)
        return s("//textarea").get(query.value)


class ModuleLine:
    def __init__(self, element: Element):
        self.element = element

    @property
    def name(self) -> Element:
        return self.element.ss("td")[1].s("strong")

    @property
    def description(self) -> Element:
        return self.element.ss("td > div.x-grid-cell-inner")[2]

    @property
    def version(self) -> Element:
        return self.element.ss("td > div.x-grid-cell-inner")[3]

    def is_syncing(self) -> bool:
        return self.version.get(query.text).strip().lower() == "syncing"

    @property
    def dashboard_button(self) -> Element:
        return self.element.ss("td > div.x-grid-cell-inner")[4].s("a")

    def open_dashboard(self):
        self.dashboard_button.click()
        return ModuleDashboard()


class ModulesPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(
            be.not_.visible, timeout=20
        )
        s("div.x-grid-buffered-loader").should(be.not_.visible, timeout=10)
        s("[id^=breadcrumbs]").should(have.text("Modules"))
        components.search().should(be.visible)

    @property
    def search(self) -> components.search:
        return components.search()

    def open_new_module(self) -> CreateModulePage:
        components.button("New Module").click()
        return CreateModulePage()

    @property
    def reload_button(self) -> components.button:
        return components.button(icon="refresh")

    @property
    def modules(self) -> [ModuleLine]:
        return [ModuleLine(p) for p in ss('table.x-grid-item').filtered_by(be.visible)]
