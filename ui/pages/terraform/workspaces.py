import typing as tp

from selene.elements import SeleneElement
from selene.api import s, ss, by, browser, be

from .base import TfBasePage, BasePage
from ui.utils.components import button, combobox, toggle, loading_modal, input, search


class CreateWorkspaceModal(BasePage):
    @staticmethod
    def wait_page_loading():
        s('div#loading').should(be.not_.visible, timeout=20)
        s('div[style*="19000"]').s(by.xpath('//div[text()="New Workspace"]')).should(be.visible, timeout=20)

    def __init__(self):
        self.form_main = ss('div[id^="workspaceform"] > fieldset')[0]
        self.form_additional = ss('div[id^="workspaceform"] > fieldset')[1]
        self._vcs_provider = combobox('VCS Provider')
        self._repository = combobox('Repository')
        self._terraform_version = combobox('Terraform Version')

    @property
    def name(self) -> input:
        return input(label='Name')

    @property
    def vcs_provider(self) -> combobox:
        return self._vcs_provider

    @property
    def repository(self) -> combobox:
        return self._repository

    @property
    def terraform_version(self) -> combobox:
        return self._terraform_version

    @property
    def auto_apply(self) -> toggle:
        return toggle('Auto Apply')

    def toggle_additional(self) -> SeleneElement:
        return s('div[componentid="additional-legendToggle"]').click()

    def set_vcs(self, workspace_type: str = 'bind'):
        """workspace type can be bind or upload"""
        if workspace_type == 'bind':
            self.form_main.ss('td.x-form-radio-group input')[0].click()
        elif workspace_type == 'upload':
            self.form_main.ss('td.x-form-radio-group input')[1].click()

    @property
    def branch(self) -> combobox:
        return combobox('Branch')

    @property
    def subdirectory(self) -> input:
        return input('Subdirectory')

    @property
    def work_directory(self) -> input:
        return input('Terraform Work Directory')

    @property
    def save_button(self) -> button:
        return button('Save')

    @property
    def cancel_button(self) -> button:
        return button('Cancel')

    
class WorkspaceLine:
    def __init__(self, element: browser.element):
        self.element = element

    @property
    def name(self) -> str:
        return self.element.ss('td')[0].s('a').text

    @property
    def last_run(self) -> str:
        return self.element.ss('td')[1].text.strip()

    @property
    def changed_on(self) -> str:
        return self.element.ss('td')[2].text.strip()

    @property
    def created_by(self) -> str:
        return self.element.ss('td')[3].text.strip()

    @property
    def repository(self) -> str:
        return self.element.ss('td')[4].text.strip()

    @property
    def launch_button(self) -> browser.element:
        return button(ticon='launch')

    @property
    def gv_button(self) -> browser.element:
        return button(ticon='variables')

    @property
    def dashboard_button(self) -> button:
        return button(qtip='Dashboard')

    def open_dashboard(self) :
        self.dashboard_button.click()
        return WorkspaceDashboard()
        

class WorkspacePage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s('div#loading').should(be.not_.existing, timeout=20)
        loading_modal('Loading...').should(be.not_.visible, timeout=10)

    @property
    def workspaces(self) -> [WorkspaceLine]:
        return [WorkspaceLine(p) for p in ss('tr.x-grid-row') if p.is_displayed()]

    def open_new_workspace(self) -> browser.element:
        button('New Workspace').click()
        return CreateWorkspaceModal()

    @property
    def search(self) -> search:
        return search()

    @property
    def ws_page(self) -> browser.element:
        return s(by.xpath("//span[text()='Workspaces']/ancestor::span"))


class WorkspaceDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal('Loading...').should(be.not_.visible, timeout=10)
        s(by.xpath("//label/span[text()='ID']/ancestor::label/following-sibling::div/div")).should(be.not_.visible, timeout=20)
    
    @property
    def launch_button(self) -> button:
        return button(ticon='launch')

    @property
    def configure_button(self) -> button:
        return button(ticon='configure')

    @property
    def delete_button(self) -> button:
        return button(icon='delete')

    @property
    def id(self) -> SeleneElement:
        return s(by.xpath("//label/span[text()='ID']/ancestor::label/following-sibling::div/div"))

    @property
    def name(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Name']/ancestor::label/following-sibling::div/div"))

    @property
    def repository(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Repository']/ancestor::label/following-sibling::div/div")) 

    @property
    def subdirectory(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Subdirectory']/ancestor::label/following-sibling::div/div")) 
    
    @property
    def terraform_version(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Terraform version']/ancestor::label/following-sibling::div/div"))

    @property
    def сonfiguration_version(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Configuration version']/ancestor::label/following-sibling::div/div"))

    @property
    def locking(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Locking']/ancestor::label/following-sibling::div/div"))

    @property
    def auto_apply(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Auto Apply']/ancestor::label/following-sibling::div/div"))

    @property
    def tags(self) -> SeleneElement: 
        return s(by.xpath("//label/span[text()='Tags']/ancestor::label/following-sibling::div/div"))


class DeleteWorkspaceModal():
    @staticmethod
    def wait_page_loading():
        s('div#loading').should(be.not_.visible, timeout=20)
        s(by.xpath("//span[text()='Cancel']/ancestor::span")).should(be.visible)

    @property
    def visible_button(self) -> browser.element:
        return s(by.xpath("//span[text()='Delete']/ancestor::span")).should(be.visible)

    @property
    def input_ws(self): 
        return s(by.xpath("//input[@placeholder='Enter the name of the Workspace to be deleted']"))

    @property
    def delete_ws(self):     #confirm delete ws
        return s(by.xpath("//span[text()='Delete']/ancestor::span"))

    @property
    def cancel_delete_button(self):
        return s(by.xpath("//span[text()='Cancel']/ancestor::span"))