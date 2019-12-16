from selene.api import s, ss, by, browser
from selene.conditions import visible
from selenium.common.exceptions import TimeoutException

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
        s('#loading').should_not_be(visible, timeout=20)

    def set_username(self, username: str):
        s('input[name=scalrLogin]').set(username)

    def set_password(self, password: str):
        s('input[name=scalrPass]').set(password)

    def submit(self):
        ss(by.xpath('//span[text()="Login"]/ancestor::a'))[1].click()
        loading_panel = s(by.xpath('//div[text()="Loading page ..." and contains(@class, "x-title-text")]'))
        loading_panel.should_be(visible)
        loading_panel.should_not_be(visible, timeout=10)
        url = browser.driver().current_url

        if '/admin/dashboard' in url:
            return AdminDashboard()
        elif '/account/dashboard' in url:
            return AccountDashboard()
        else:
            components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should_not_be(visible)
            try:
                s(by.xpath('//strong[text()="Getting started"]')).should_be(visible, timeout=1)
                return TerraformEnvDashboard()
            except TimeoutException:
                return ClassicEnvDashboard()
        # raise AssertionError(f'Current url: {url} but dashboard not exist')
