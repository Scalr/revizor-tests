from selene.api import s, by

from ui.pages.terraform.dashboard import TerraformEnvDashboard
from ui.pages.terraform.vcs import VCSPage
from ui.pages.terraform.workspaces import WorkspacePage


class TfTopMenu:
    def open_dashboard(self) -> TerraformEnvDashboard:
        s(
            by.xpath('//span[contains(@class, "x-btn-inner-default-toolbar-small") and text()="Dashboard"]/ancestor::a')
        ).click()
        return TerraformEnvDashboard()

    def open_vcs_providers(self) -> VCSPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text()="VCS"]/ancestor::a')).click()
        return VCSPage()

    def open_workspaces(self) -> WorkspacePage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Workspaces"]/ancestor::a')).click()
        return WorkspacePage()
