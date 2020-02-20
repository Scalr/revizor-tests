import time

import pytest
from _pytest.fixtures import FixtureRequest

from selene.core.entity import Element, Collection
from selene.api import browser, s, ss, be, query

from revizor2.conf import CONF
from revizor2.testenv import TestEnv

from ui.utils import consts
from ui.utils import components
from pages.login import LoginPage


class TestPagesForErrors:
    testenv: TestEnv
    topmenu_button: Element = s('a[data-qa-id="topmenu-mainmenu-btn"]')
    topmenu: Element
    menu_scrolldown: Element
    menu_items: Collection

    @pytest.fixture(autouse=True)
    def skip_warning_tests(self, request: FixtureRequest):
        if request.node.name.startswith('test_account_scope_pages') and self.base_url == '/index7.html':
            pytest.skip('https://scalr-labs.atlassian.net/browse/SCALRCORE-14849')
        elif self.base_url == '/index7.html':
            pytest.skip('https://scalr-labs.atlassian.net/browse/SCALRCORE-14711')

    @pytest.fixture(autouse=True, params=["/", "/index7.html"], ids=['extjs5', 'extjs7'])
    def set_baseurl(self, request: FixtureRequest, testenv: TestEnv):
        self.testenv = testenv
        self.base_url = request.param
        yield
        self.assert_errors()
        browser.driver().delete_all_cookies()

    def assert_errors(self):
        if browser.config.browser_name.lower().startswith('firefox'):
            return
        driver = browser.driver()
        logs = driver.get_log("browser")
        for log in logs:
            if log["source"] == "network":
                continue
            raise AssertionError(f"Browser has an error in console: {logs}")

    def authorize(self, username: str, password: str):
        browser.open(
            f"https://{self.testenv.te_id}.test-env.scalr.com{self.base_url}"
        )
        s("#loading").should(be.not_.visible, timeout=20)
        login_page = LoginPage()
        login_page.set_idp_provider('scalr')
        login_page.set_username(username)
        login_page.set_password(password)
        login_page.submit()

    def get_menu_items_count(self):
        self.topmenu_button.click()
        attr = 'componentid'
        if '7' in self.base_url:
            attr = 'data-componentid'
        self.topmenu = s('div[data-qa-id="{}-menu"]'.format(
            self.topmenu_button.get(query.attribute(attr))
        ))
        self.topmenu.should(be.visible)
        menu_items_count = len(self.scalr_menu_items)
        self.topmenu_button.click()
        self.topmenu.should(be.not_.visible)
        time.sleep(1)
        return menu_items_count

    def iterate_scalr_menu(self):
        items_count = self.get_menu_items_count()
        for i in range(1, items_count):
            self.topmenu_button.click()
            self.topmenu.should(be.visible)
            while not self.scalr_menu_items[i].matching(be.visible):
                self.scalr_menu_scrolldown.click()
            ss("div.x-mask").should(be.not_.visible)
            self.scalr_menu_items[i].element('..').hover().click()
            components.loading_modal(
                consts.LoadingModalMessages.LOADING_PAGE
            ).should(be.not_.visible, timeout=10)
            ss("div.x-mask").should(be.not_.visible)
            self.assert_errors()

    @property
    def scalr_menu_scrolldown(self):
        return self.topmenu.s("div.x-box-scroller-bottom")

    @property
    def scalr_menu_items(self):
        return self.topmenu.ss(
            "div.x-menu-item[id^=menuitem] > a.x-menu-item-link-href"
        )

    def test_global_scope_pages(self):
        self.authorize(
            CONF.credentials.testenv.accounts.super_admin.username,
            CONF.credentials.testenv.accounts.super_admin.password,
        )

        self.iterate_scalr_menu()

    def test_account_scope_pages(self):
        self.authorize(
            CONF.credentials.testenv.accounts.admin.username,
            CONF.credentials.testenv.accounts.admin.password,
        )
        # go to account scope
        s("a.x-btn-environment").click()
        s("div.x-menu-environment").should(be.visible)
        s("div.x-menu-favorite-account-container").element('..').click()
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(
            be.visible
        ).should(be.not_.visible, timeout=10)
        ss("div.x-mask").should(be.not_.visible)

        self.iterate_scalr_menu()

    @pytest.mark.parametrize(
        'username,password', [
            pytest.param(CONF.credentials.testenv.accounts.default.username,
                         CONF.credentials.testenv.accounts.default.password, id="classic_env"),
            pytest.param(CONF.credentials.testenv.accounts.terraform.username,
                         CONF.credentials.testenv.accounts.terraform.password, id="terraform_env")
        ]
    )
    def test_environment_scope_pages(self, username: str, password: str):
        self.authorize(username, password)
        s("div.x-mask").should(be.not_.visible)

        self.iterate_scalr_menu()

