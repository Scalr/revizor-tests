# coding: utf-8
"""
Created on 01.11.18
@author: Eugeny Kurkovich
"""

import pytest

from revizor2.conf import CONF
from pages.login import LoginPage
from elements.base import TableRow

from selenium.common.exceptions import NoSuchElementException

USER = CONF.credentials.testenv.accounts.admin['username']
PASSWORD = CONF.credentials.testenv.accounts.admin['password']

TE_ID = "f95c6e105105"


class TestAccounts(object):

    test_account_name = "Selenium"

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, request):
        load_timeout = request.config.getoption("load_timeout")
        self.driver = selenium
        self.driver.implicitly_wait(10)
        #self.container = testenv
        login_page = LoginPage(
            self.driver,
            #'http://%s.test-env.scalr.com' % self.container.te_id).open()
            'http://%s.test-env.scalr.com' % TE_ID,
            timeout=load_timeout
        ).open()
        self.admin_dashboard = login_page.login(USER, PASSWORD)

    def test_create_account(self):
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.new_account()
        account_edit_popup.name_field.write(self.test_account_name)
        account_edit_popup.select_account_owner("AccountSuperAdmin")
        account_edit_popup.comments_field.write("Selenium test new account")
        account_edit_popup.cost_centers_field.select(option='Default cost centre', hide_options=True)
        account_edit_popup.create_button.click()
        TableRow(driver=accounts_page.driver, label=self.test_account_name).get_element()

    def test_delete_account(self):
        accounts_page = self.admin_dashboard.go_to_accounts()
        table_row = TableRow(driver=accounts_page.driver, label=self.test_account_name)
        table_row.check()
        confirm_panel = accounts_page.delete_account_button.click()
        confirm_panel.click_by_label('Delete')
        with pytest.raises(NoSuchElementException):
            table_row.get_element(refresh=True)

