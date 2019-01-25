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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER = CONF.credentials.testenv.accounts.admin['username']
PASSWORD = CONF.credentials.testenv.accounts.admin['password']


class TestAccounts(object):

    test_account_name = "Selenium"

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, request, testenv):
        load_timeout = request.config.getoption("load_timeout")
        self.driver = selenium
        self.driver.implicitly_wait(3)
        login_page = LoginPage(
            self.driver,
            f'http://{testenv.te_id}.test-env.scalr.com',
            timeout=load_timeout
        ).open()
        self.admin_dashboard = login_page.login(USER, PASSWORD)

    def test_create_account(self):
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.new_account_click()
        account_edit_popup.name_field.write(self.test_account_name)
        # Create new account owner
        account_owner_popup = account_edit_popup.new_account_owner_click()
        account_owner_popup.full_name_field.write(self.test_account_name)
        account_owner_popup.email_field.write("selenium@localhost.net")
        account_owner_popup.comments_field.write("new account owner")
        account_owner_popup.generate_password_button.check()
        account_owner_popup.set_activate_button.click()
        account_owner_popup.set_global_admin_perm_button.check()
        owner_password_detail_panel = account_owner_popup.save_button.click(panel_type='form')
        WebDriverWait(self.driver, 3).until(
            EC.invisibility_of_element_located(account_owner_popup.save_button.locator))
        owner_password_detail_panel.click_by_label('Close')
        # Select created account owner
        account_edit_popup.set_account_owner(self.test_account_name)
        account_edit_popup.comments_field.write("Selenium test new account")
        account_edit_popup.cost_centers_field.select(option='Default cost centre', hide_options=True)
        account_edit_popup.create_button.click()
        assert TableRow(driver=accounts_page.driver, label=self.test_account_name).exists

    def test_edit_account(self):
        new_account = '-'.join((self.test_account_name, 'edited'))
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.edit_account_click(label=self.test_account_name)
        account_edit_popup.name_field.write(new_account)
        account_edit_popup.save_button.click()
        assert TableRow(driver=accounts_page.driver, label=new_account).exists

    def test_delete_account(self):
        account_name = '-'.join((self.test_account_name, 'edited'))
        accounts_page = self.admin_dashboard.go_to_accounts()
        table_row = TableRow(driver=accounts_page.driver, label=account_name)
        table_row.check()
        confirm_panel = accounts_page.delete_account_button.click()
        confirm_panel.click_by_label('Delete')
        with pytest.raises(NoSuchElementException):
            table_row.get_element(reload=True)

