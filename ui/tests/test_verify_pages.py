import time

import pytest
from _pytest.fixtures import FixtureRequest

from selene.api import browser, s, ss
from selene.conditions import visible

from revizor2.conf import CONF
from revizor2.testenv import TestEnv

from ui.utils import consts
from ui.utils import components
from pages.login import LoginPage


class TestPagesForErrors:
    testenv: TestEnv
    topmenu_button: browser.SeleneElement = s('a.x-btn-scalr')
    topmenu: browser.SeleneElement
    menu_scrolldown: browser.SeleneElement
    menu_items: browser.SeleneCollection

    @pytest.fixture(autouse=True, params=['/', '/index7.html'])
    def cleanup_cookies(self, request: FixtureRequest,  testenv: TestEnv):
        self.testenv = testenv
        self.base_url = request.param
        yield
        self.assert_errors()
        browser.driver().delete_all_cookies()

    def assert_errors(self):
        driver = browser.driver()
        logs = driver.get_log('browser')
        for log in logs:
            if log['source'] == 'network':
                continue
            raise AssertionError(f'Browser has an error in console: {logs}')

    def authorize(self, username, pasword):
        browser.open_url(f'https://{self.testenv.te_id}.test-env.scalr.com{self.base_url}')
        s('#loading').should_not_be(visible, timeout=20)
        login_page = LoginPage()
        login_page.set_username(username)
        login_page.set_password(pasword)
        login_page.submit()

    def get_menu_items_count(self, menu_selector: str):
        self.topmenu_button.click()
        self.topmenu = s(f'div.{menu_selector}')
        self.topmenu.should_be(visible)
        menu_items_count = len(self.scalr_menu_items)
        self.topmenu_button.click()
        self.topmenu.should_not_be(visible)
        time.sleep(1)
        return menu_items_count

    def iterate_scalr_menu(self, items_count: int):
        for i in range(1, items_count):
            self.topmenu_button.click()
            self.topmenu.should_be(visible)
            while not self.scalr_menu_items[i].is_displayed():
                self.scalr_menu_scrolldown.click()
            ss('div.x-mask').should_not_be(visible)
            self.scalr_menu_items[i].parent_element.hover().click()
            components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should_not_be(visible, timeout=10)
            ss('div.x-mask').should_not_be(visible)
            self.assert_errors()

    @property
    def scalr_menu_scrolldown(self):
        return self.topmenu.s('div.x-box-scroller-bottom')

    @property
    def scalr_menu_items(self):
        return self.topmenu.ss('div.x-menu-item[id^=menuitem] > a.x-menu-item-link-href')

    def test_global_scope_pages(self):
        self.authorize(CONF.credentials.testenv.accounts.super_admin.username,
                       CONF.credentials.testenv.accounts.super_admin.password)
        menu_items = self.get_menu_items_count('x-menu-scalr')
        self.iterate_scalr_menu(menu_items)

    def test_account_scope_pages(self):
        self.authorize(CONF.credentials.testenv.accounts.admin.username,
                       CONF.credentials.testenv.accounts.admin.password)
        # go to account scope
        s('a.x-btn-environment').click()
        s('div.x-menu-environment').should_be(visible)
        s('div.x-menu-favorite-account-container').parent_element.click()
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should_be(visible).should_not_be(visible,
                                                                                                            timeout=10)
        ss('div.x-mask').should_not_be(visible)

        menu_items = self.get_menu_items_count('x-menu-account')
        self.iterate_scalr_menu(menu_items)

    def test_classic_environment_scope_pages(self):
        self.authorize(CONF.credentials.testenv.accounts.admin.username,
                       CONF.credentials.testenv.accounts.admin.password)
        s('div.x-mask').should_not_be(visible)

        menu_items = self.get_menu_items_count('x-menu-environment')
        self.iterate_scalr_menu(menu_items)

    def test_nextgen_environment_scope_pages(self):
        self.authorize(CONF.credentials.testenv.accounts.terraform.username,
                       CONF.credentials.testenv.accounts.terraform.password)

        s('div.x-mask').should_not_be(visible)

        menu_items = self.get_menu_items_count('x-menu-environment')
        self.iterate_scalr_menu(menu_items)
