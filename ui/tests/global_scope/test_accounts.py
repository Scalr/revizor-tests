# coding: utf-8
"""
Created on 01.11.18
@author: Eugeny Kurkovich
"""

import pytest

from selenium.common.exceptions import NoSuchElementException

from revizor2.conf import CONF
from pages.login import LoginPage
from elements import locators
from elements.base import Label, Button

USER = CONF.credentials.testenv.accounts.admin['username']
PASSWORD = CONF.credentials.testenv.accounts.admin['password']

TE_ID = "faff2aed07fa"


class TestAccounts(object):

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium):
        self.driver = selenium
        self.driver.implicitly_wait(10)
        #self.container = testenv
        login_page = LoginPage(
            self.driver,
            #'http://%s.test-env.scalr.com' % self.container.te_id).open()
            'http://%s.test-env.scalr.com' % TE_ID).open()
        self.admin_dashboard = login_page.login(USER, PASSWORD)

    def test_create_account(self):
        import time
        accounts_page = self.admin_dashboard.go_to_accounts()
        edit_popup = accounts_page.open_edit_popup()
        edit_popup.name_field.write("Selenium")
        edit_popup.select_account_owner("test")
        time.sleep(3)
        edit_popup.comments_field.write("Selenium test new account")
        edit_popup.cost_centers_field.select(option='Default cost centre', hide_options=True)
        edit_popup.create_button.click()
        time.sleep(10)
