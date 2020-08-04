import typing as tp
import time

from selene.core.entity import Element
from selene.api import s, ss, by, browser, be, have

from .base import TfBasePage, BasePage
from ui.pages.terraform.runs import WorkspaceRunsPage
from ui.utils.components import button, combobox, toggle, loading_modal, input, search


class CreateWorkspaceFromVCS(BasePage):
    @staticmethod
    def wait_page_loading():
        ss(by.xpath("//div[text()='Configure workspace']")).element_by(be.visible).with_(timeout=10).should(be.visible)

    @property
    def name(self) -> input:
        return input(label="Name")

    @property
    def vcs_provider(self) -> combobox:
        return combobox("VCS provider")

    @property
    def repository(self) -> combobox:
        return combobox("Repository")

    @property
    def terraform_version(self) -> combobox:
        return combobox("Terraform version")

    @property
    def auto_apply(self) -> toggle:
        return toggle("Auto apply")

    @property
    def toggle_additional(self) -> Element:
        return ss(by.xpath("//div[text()='Advanced']")).element_by(be.visible)

    @property
    def branch(self) -> combobox:
        return combobox("Branch")

    @property
    def subdirectory(self) -> input:
        return input("Subdirectory")

    @property
    def work_directory(self) -> input:
        return input("Terraform work directory")

    def create(self) -> "WorkspaceDashboard":
        self.create_button.click()
        return WorkspaceDashboard()

    @property
    def create_button(self) -> button:
        return button("Create")

    @property
    def cancel_button(self) -> button:
        return button("Cancel")


class CreateWorkspacePage(BasePage):
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//div[text()='New Workspace']")).should(be.visible).with_(timeout=10)

    def __init__(self):
        self.element = s(
            by.xpath(
                '//div[starts-with(@id, "workspaceform") and contains(@id, "body")]/ancestor::div'
            )
        )
        self.form_main = ss('div[id^="workspaceform"] > fieldset')[0]
        self.form_additional = ss('div[id^="workspaceform"] > fieldset')[1]

    def open_from_registry_form(self):
        s(by.xpath("//*[text()='From registry']/ancestor::div[2]")).click()
        raise NotImplemented("This page not implemented")

    def open_from_vcs_form(self) -> CreateWorkspaceFromVCS:
        s(by.xpath("//*[text()='From VCS repository']/ancestor::div[2]")).click()
        return CreateWorkspaceFromVCS()

    def open_from_cli_form(self):
        s(by.xpath("//*[text()='From Terraform CLI or API]/ancestor::div[2]")).click()
        raise NotImplemented("This page not implemented")


class WorkspaceLine:
    def __init__(self, element: Element):
        self.element = element

    @property
    def name(self) -> Element:
        return self.element.ss("td")[0].s("a")

    @property
    def last_run(self) -> Element:
        return self.element.ss("td")[1]

    @property
    def changed_on(self) -> Element:
        return self.element.ss("td")[2]

    @property
    def created_by(self) -> Element:
        return self.element.ss("td")[3]

    @property
    def repository(self) -> Element:
        return self.element.ss("td")[4]

    @property
    def launch_button(self) -> button:
        return button(ticon="launch", parent=self.element)

    @property
    def gv_button(self) -> button:
        return button(ticon="variables", parent=self.element)

    @property
    def dashboard_button(self) -> button:
        return button(qtip="Dashboard", parent=self.element)

    def open_dashboard(self) -> "WorkspaceDashboard":
        self.dashboard_button.click()
        return WorkspaceDashboard()

    def open_variable_dashboard(self) -> "WorkspaceVariablePage":
        self.gv_button.click()
        return WorkspaceVariablePage()

    def open_runs_page(self) -> "WorkspaceRunsPage":
        self.open_dashboard()
        button(title="Runs").click()
        return WorkspaceRunsPage()


class WorkspacePage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.existing, timeout=20)
        loading_modal("Loading...").should(be.not_.visible, timeout=10)
        ss("div.x-grid-buffered-loader").should(be.not_.visible, timeout=10)

    @property
    def workspaces(self) -> [WorkspaceLine]:
        return [WorkspaceLine(p) for p in ss("div.x-grid.x-panel-column-left tr.x-grid-row") if p.is_displayed()]

    def open_new_workspace(self) -> CreateWorkspacePage:
        button('New Workspace').click()
        return CreateWorkspacePage()

    @property
    def search(self) -> search:
        return search()

    @property
    def empty_ws_table(self) -> Element:
        return s(by.xpath("//div[text()='No Workspaces found.']"))

    @property
    def reload_button(self) -> button:
        return button(icon="refresh")

    def reload(self):
        self.reload_button.click()
        ss("div.x-grid-buffered-loader").should(be.visible, timeout=10)
        ss("div.x-grid-buffered-loader").should(be.not_.visible, timeout=10)
        time.sleep(0.5)


class WorkspaceDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal("Loading page...").should(be.not_.visible, timeout=10)
        s(by.xpath("//div[text()='Workspace']")).with_(timeout=20).should(
            be.visible
        )

    @property
    def launch_button(self) -> button:
        return button(ticon="launch")

    @property
    def configure_button(self) -> button:
        return button(ticon="configure")

    @property
    def delete_button(self) -> button:
        return button(icon="delete")

    @property
    def id(self) -> Element:
        return s(by.xpath("//span[text()='ID']/ancestor::label/following-sibling::div/div"))

    @property
    def name(self) -> Element:
        return s(by.xpath("//span[text()='Name']/ancestor::label/following-sibling::div/div"))

    @property
    def repository(self) -> Element:
        return s(
            by.xpath("//span[text()='Repository']/ancestor::label/following-sibling::div/div")
        )

    @property
    def subdirectory(self) -> Element:
        return s(
            by.xpath(
                "//span[text()='Subdirectory']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def terraform_version(self) -> Element:
        return s(
            by.xpath(
                "//span[text()='Terraform version']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def configuration_version(self) -> Element:
        return s(
            by.xpath(
                "//span[text()='Configuration version']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def locking(self) -> Element:
        return s(
            by.xpath("//span[text()='Locking']/ancestor::label/following-sibling::div/div")
        )

    @property
    def auto_apply(self) -> toggle:
        return toggle("Auto Apply")

    @property
    def tags(self) -> Element:
        return s(by.xpath("//span[text()='Tags']/ancestor::label/following-sibling::div/div"))


class DeleteWorkspaceModal:
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s("div.message").should(have.text("Delete Workspace:"))

    @property
    def input_name(self):
        return s(by.xpath("//input[@placeholder='Enter the name of the Workspace to be deleted']"))

    @property
    def delete_button(self) -> button:  # confirm delete ws
        return button("Delete")

    @property
    def cancel_button(self) -> button:
        return button("Cancel")


class EnvVariableLine:
    def __init__(self, element: browser.element):
        self.element = element

    @property
    def name(self) -> Element:
        return self.element.ss('td[@data-columnid="name"]//input')

    @property
    def value(self) -> Element:
        return self.element.ss('td[@data-columnid="value"]//input')

    @property
    def sensitive_button(self) -> button:
        return button(title="Sensitive", parent=self.element)

    @property
    def delete_button(self) -> button:
        return button(qtip="Delete", parent=self.element)

    @property
    def input_name(self):
        return self.element.ss(".//td[@data-columnid='name']//input")[-1]

    @property
    def input_value(self):
        return self.element.ss(".//td[@data-columnid='value']//input")[-1]


class TFVariableLine(EnvVariableLine):
    @property
    def hcl_button(self) -> button:
        return button(title="HCL", parent=self.element)


class WorkspaceVariablePage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal("Loading...").should(be.not_.visible, timeout=10)
        s(by.xpath("//span[text()='Save']/ancestor::span")).should(be.visible, timeout=20)
        s(by.xpath("//div[contains(text(),'Environment Variable')]/ancestor::fieldset//tr")).should(
            be.visible, timeout=20
        )

    @property
    def tf_variables(self) -> [TFVariableLine]:
        return [
            TFVariableLine(p)
            for p in ss('//div[contains(text(),"Terraform Variable")]/ancestor::fieldset//tr')
            if p.is_displayed()
        ]

    @property
    def env_variables(self) -> [EnvVariableLine]:
        return [
            EnvVariableLine(p)
            for p in ss('//div[contains(text(),"Environment Variable")]/ancestor::fieldset//tr')
            if p.is_displayed()
        ]

    # @property
    # def search(self) -> search:
    #     parent = s(by.xpath("//div[starts-with(@id, 'workspacevariablesearchfield')]"))
    #     return search(parent)

    @property
    def new_tf_variable(self) -> button:
        button(title="New Variable").click()
        return button(title="New Terraform Variable")

    @property
    def new_env_variable(self) -> button:
        button(title="New Variable").click()
        return button(title="New Environment Variable")

    @property
    def refresh(self) -> button:
        return s(
            by.xpath(
                "//div[starts-with(@id, 'workspacedashboardvariables')]//a[@data-qtip='Refresh']"
            )
        )

    @property
    def save(self) -> button:
        return button(title="Save")

    @property
    def empty_tf_variable(sefl) -> Element:
        return s(by.xpath("//div[text()='You have no variables added yet.']"))
