import time
import typing as tp

from selene.api import s, ss, by, browser, be, query

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

    def set_idp_provider(self, name: str = 'scalr'):
        providers = components.combobox('Identity Provider')
        providers.set_value(name)
        time.sleep(1)

    def submit(self) -> tp.Union[AdminDashboard, AccountDashboard, TerraformEnvDashboard, ClassicEnvDashboard]:
        ss(by.xpath('//span[text()="Login"]/ancestor::a'))[1].click()
        loading_panel = components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE)
        loading_panel.should(be.not_.visible, timeout=10)
        topmenu = ss('div.x-toolbar.x-topmenu-menu').filtered_by(be.visible)[0].should(be.visible)
        s(by.xpath('//span[contains(@class, "x-btn-inner-default-toolbar") and contains(text(), "Dashboard")]/ancestor::a')).should(be.visible).should(be.clickable)
        url = browser.driver().current_url

        if '/admin/dashboard' in url:
            return AdminDashboard()
        elif '/account/dashboard' in url:
            return AccountDashboard()
        else:
            if 'SourceSansProRegular' in topmenu.get(query.css_property('font-family')):
                return TerraformEnvDashboard()
            else:
                return ClassicEnvDashboard()
