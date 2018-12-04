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

TE_ID = "f95c6e105105"


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
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.new_account()
        account_edit_popup.name_field.write("Selenium")
        account_edit_popup.select_account_owner("AccountSuperAdmin")
        account_edit_popup.comments_field.write("Selenium test new account")
        account_edit_popup.cost_centers_field.select(option='Default cost centre', hide_options=True)
        account_edit_popup.create_button.click()
