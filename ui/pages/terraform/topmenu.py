from selene.api import s, by
from selenium.webdriver.common.keys import Keys

from ui.pages.terraform import dashboard, vcs, workspaces, modules, gv, offerings


# TODO: Add breadcrumbs element
class TfTopMenu:
    def open_dashboard(self) -> dashboard.TerraformEnvDashboard:
        s(
            by.xpath('//span[contains(@class, "x-btn-inner-default-toolbar-small") and text()="Dashboard"]/ancestor::a')
        ).click()
        return dashboard.TerraformEnvDashboard()

    def open_vcs_providers(self) -> vcs.VCSPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text()="VCS"]/ancestor::a')).click()
        return vcs.VCSPage()

    def open_workspaces(self) -> workspaces.WorkspacePage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Workspaces"]/ancestor::a')).click()
        return workspaces.WorkspacePage()

    def open_modules(self) -> modules.ModulesPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Modules"]/ancestor::a')).click()
        return modules.ModulesPage()

    def open_gv(self) -> gv.GVPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="GV"]/ancestor::a')).click()
        return gv.GVPage()

    def open_offerings_request(self) -> offerings.OfferingsRequestPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Offerings"]/ancestor::a')).click()
        s(by.xpath(
            '//span[contains(@class, "x-menu-item-indent") and text()="Request"]/ancestor::a'
        )).click()
        return offerings.OfferingsRequestPage()

    def open_offerings_management(self) -> offerings.OfferingsManagementPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Offerings"]/ancestor::a')).click()
        s(by.xpath(
            '//span[contains(@class, "x-menu-item-indent") and text()="Management"]/ancestor::a'
        )).click()
        return offerings.OfferingsManagementPage()

    def open_offerings_categories(self) -> offerings.OfferingsCategoriesPage:
        s(by.xpath(
            '//span[contains(@class, "x-btn-inner-default-toolbar-small") and text('
            ')="Offerings"]/ancestor::a')).click()
        s(by.xpath(
            '//span[contains(@class, "x-menu-item-indent") and text()="Categories"]/ancestor::a'
        )).click()
        return offerings.OfferingsCategoriesPage()
