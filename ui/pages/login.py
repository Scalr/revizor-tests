from selene.api import s, ss, by, browser, be, have
from selene.core.exceptions import TimeoutException

from ui.utils import consts
from ui.utils import components
from ui.pages.base import BasePage
from ui.pages.admin.dashboard import AdminDashboard
from ui.pages.account.dashboard import AccountDashboard
from ui.pages.classic.dashboard import ClassicEnvDashboard
from ui.pages.terraform.dashboard import TerraformEnvDashboard


class LoginPage(BasePage):

    @staticmethod
    def wait_page_loading():
        s('#loading').should(be.not_.visible, timeout=20)

    def set_username(self, username: str):
        s('input[name=scalrLogin]').set_value(username)

    def set_password(self, password: str):
        s('input[name=scalrPass]').set_value(password)

    def submit(self):
        ss(by.xpath('//span[text()="Login"]/ancestor::a'))[1].click()
        loading_panel = s(by.xpath('//div[text()="Loading page ..." and contains(@class, "x-title-text")]'))
        # loading_panel.should(be.visible)
        loading_panel.should(be.not_.visible, timeout=10)
        url = browser.driver().current_url

        if '/admin/dashboard' in url:
            return AdminDashboard()
        elif '/account/dashboard' in url:
            return AccountDashboard()
        else:
            components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible)
            try:
                ss(by.xpath('//*[normalize-space(text())="Getting started"]')).should(have.size(2), timeout=10)
                ss(by.xpath('//*[normalize-space(text())="Getting started"]')).filtered_by(be.visible).should(have.size(1))
                return TerraformEnvDashboard()
            except TimeoutException:
                return ClassicEnvDashboard()
        # raise AssertionError(f'Current url: {url} but dashboard not exist')
