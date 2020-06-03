import typing as tp


from selene.elements import SeleneElement
from selene.api import s, ss, by, browser, be

from .base import TfBasePage, BasePage
from ui.pages.terraform.runs import WorkspaceRunsPage
from ui.utils.components import button, combobox, toggle, loading_modal, input, search


class CreateWorkspaceModal(BasePage):
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s("div[id^=workspaceform]").s(by.xpath('//div[text()="New Workspace"]')).should(
            be.visible, timeout=20
        )
        s("div[id^=workspaceform][id$=body]").should(be.visible)

    def __init__(self):
        self.element = s(
            by.xpath(
                '//div[starts-with(@id, "workspaceform") and contains(@id, "body")]/ancestor::div'
            )
        )
        self.form_main = ss('div[id^="workspaceform"] > fieldset')[0]
        self.form_additional = ss('div[id^="workspaceform"] > fieldset')[1]

    @property
    def name(self) -> input:
        return input(label="Name", parent=self.form_main)

    @property
    def vcs_provider(self) -> combobox:
        return combobox("VCS Provider", self.form_main)

    @property
    def repository(self) -> combobox:
        return combobox("Repository", self.form_main)

    @property
    def terraform_version(self) -> combobox:
        return combobox("Terraform Version", self.form_main)

    @property
    def auto_apply(self) -> toggle:
        return toggle("Auto Apply", self.form_main)

    def toggle_additional(self) -> SeleneElement:
        return self.element.s("div#additional-legendTitle").click()

    def set_vcs(self, workspace_type: str = "bind"):
        """workspace type can be bind or upload"""
        if workspace_type == "bind":
            self.form_main.ss("td.x-form-radio-group input")[0].click()
        elif workspace_type == "upload":
            self.form_main.ss("td.x-form-radio-group input")[1].click()

    @property
    def branch(self) -> combobox:
        return combobox("Branch", self.element)

    @property
    def subdirectory(self) -> input:
        return input("Subdirectory", self.form_additional)

    @property
    def work_directory(self) -> input:
        return input("Terraform Work Directory", self.form_additional)

    @property
    def save_button(self) -> button:
        return button("Save", parent=self.element)

    @property
    def cancel_button(self) -> button:
        return button("Cancel", parent=self.element)


class WorkspaceLine:
    def __init__(self, element: SeleneElement):
        self.element = element

    @property
    def name(self) -> SeleneElement:
        return self.element.ss("td")[0].s("a")

    @property
    def last_run(self) -> SeleneElement:
        return self.element.ss("td")[1]

    @property
    def changed_on(self) -> SeleneElement:
        return self.element.ss("td")[2]

    @property
    def created_by(self) -> SeleneElement:
        return self.element.ss("td")[3]

    @property
    def repository(self) -> SeleneElement:
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
        self.dashboard_button.click()
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

    def open_new_workspace(self) -> CreateWorkspaceModal:
        button('New Workspace').click()
        return CreateWorkspaceModal()

    @property
    def search(self) -> search:
        return search()

    @property
    def empty_ws_table(self) -> SeleneElement:
        return s(by.xpath("//div[text()='No Workspaces found.']"))


class WorkspaceDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal("Loading...").should(be.not_.visible, timeout=10)
        s(by.xpath("//label/span[text()='ID']/ancestor::label/following-sibling::div/div")).should(
            be.not_.visible, timeout=20
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
    def id(self) -> SeleneElement:
        return s(by.xpath("//span[text()='ID']/ancestor::label/following-sibling::div/div"))

    @property
    def name(self) -> SeleneElement:
        return s(by.xpath("//span[text()='Name']/ancestor::label/following-sibling::div/div"))

    @property
    def repository(self) -> SeleneElement:
        return s(
            by.xpath("//span[text()='Repository']/ancestor::label/following-sibling::div/div")
        )

    @property
    def subdirectory(self) -> SeleneElement:
        return s(
            by.xpath(
                "//span[text()='Subdirectory']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def terraform_version(self) -> SeleneElement:
        return s(
            by.xpath(
                "//span[text()='Terraform version']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def configuration_version(self) -> SeleneElement:
        return s(
            by.xpath(
                "//span[text()='Configuration version']/ancestor::label/following-sibling::div/div"
            )
        )

    @property
    def locking(self) -> SeleneElement:
        return s(
            by.xpath("//span[text()='Locking']/ancestor::label/following-sibling::div/div")
        )

    @property
    def auto_apply(self) -> toggle:
        return toggle("Auto Apply")

    @property
    def tags(self) -> SeleneElement:
        return s(by.xpath("//span[text()='Tags']/ancestor::label/following-sibling::div/div"))


class DeleteWorkspaceModal:
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.visible, timeout=20)
        s(by.xpath("//span[text()='Cancel']/ancestor::span")).should(be.visible)

    @property
    def visible_button(self) -> browser.element:
        return s(by.xpath("//span[text()='Delete']/ancestor::span")).should(be.visible)

    @property
    def input_name(self):
        return s(by.xpath("//input[@placeholder='Enter the name of the Workspace to be deleted']"))

    @property
    def delete_button(self):  # confirm delete ws
        return s(by.xpath("//span[text()='Delete']/ancestor::span"))

    @property
    def cancel_delete_button(self):
        return s(by.xpath("//span[text()='Cancel']/ancestor::span"))


class EnvVariableLine:
    def __init__(self, element: browser.element):
        self.element = element

    @property
    def name(self) -> SeleneElement:
        return self.element.ss('td[@data-columnid="name"]//input')

    @property
    def value(self) -> SeleneElement:
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
    def empty_tf_variable(sefl) -> SeleneElement:
        return s(by.xpath("//div[text()='You have no variables added yet.']"))
