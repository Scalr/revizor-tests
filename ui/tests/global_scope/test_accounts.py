# coding: utf-8
"""
Created on 01.11.18
@author: Eugeny Kurkovich
"""

import pytest

from uuid import uuid4

from pages.login import LoginPage
from elements.base import TableRow, Filter

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestAccounts(object):

    test_email = "test@scalr.com"

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
        self.account_email = f"selenium-{uuid4().hex[0:8]}@localhost.net"
        self.admin_dashboard = login_page.login(
            request.config.admin_login,
            request.config.admin_pass)

    @pytest.fixture
    def get_account(self):
        account_name = f"Selenium-{uuid4().hex[0:8]}"
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.new_account_click()
        account_edit_popup.name_field.write(account_name)
        account_edit_popup.set_account_owner(f"{self.test_email}")
        account_edit_popup.comments_field.write(f"{account_name}: new account")
        account_edit_popup.cost_centers_field.select(option='Default cost centre', hide_options=True)
        account_edit_popup.create_button.click()
        account_edit_popup.create_button.wait_until_condition(EC.staleness_of, timeout=3)
        Filter(driver=accounts_page.driver).write(account_name)
        assert TableRow(driver=accounts_page.driver, label=account_name).exists
        return account_name

    def test_new_account_owner(self, get_account):
        account_name = get_account
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.edit_account_click(account_name)
        # Create new account owner
        account_owner_popup = account_edit_popup.new_account_owner_click()
        account_owner_popup.full_name_field.write(account_name)
        account_owner_popup.email_field.write(self.account_email)
        account_owner_popup.comments_field.write(f"{account_name}: new account owner")
        account_owner_popup.generate_password_button.check()
        account_owner_popup.set_activate_button.click()
        account_owner_popup.set_global_admin_perm_button.check()
        owner_password_detail_panel = account_owner_popup.save_button.click(panel_type='form')
        account_owner_popup.save_button.wait_until_condition(EC.staleness_of, timeout=3)
        owner_password_detail_panel.click(label='Close')
        # Select created account owner
        account_edit_popup.set_account_owner(self.account_email)
        account_edit_popup.save_button.click()
        account_edit_popup.save_button.wait_until_condition(EC.staleness_of, timeout=3)
        Filter(driver=accounts_page.driver).write(account_name)
        assert TableRow(driver=accounts_page.driver, label=self.account_email).exists

    def test_cancel_edit_account_owner(self, get_account):
        account_name = get_account
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.edit_account_click(label=account_name)
        account_edit_popup.set_account_owner("AccountSuperAdmin")
        account_edit_popup.cancel_button.click()
        WebDriverWait(accounts_page.driver, 3).until(
            EC.invisibility_of_element_located(account_edit_popup.cancel_button.locator))
        Filter(driver=accounts_page.driver).write(account_name)
        table_row = TableRow(driver=accounts_page.driver, label=account_name).get_element()
        assert table_row.find_elements_by_xpath(f"./descendant::* [text()='{self.test_email}']")

    def test_edit_account_name(self, get_account):
        account_name = get_account
        accounts_page = self.admin_dashboard.go_to_accounts()
        new_account = '-'.join((account_name, 'edited'))
        account_edit_popup = accounts_page.edit_account_click(label=account_name)
        account_edit_popup.name_field.write(new_account)
        account_edit_popup.save_button.click()
        account_edit_popup.save_button.wait_until_condition(EC.staleness_of)
        Filter(driver=accounts_page.driver).write(new_account)
        assert TableRow(driver=accounts_page.driver, label=new_account).exists

    def test_delete_account(self, get_account):
        account_name = get_account
        accounts_page = self.admin_dashboard.go_to_accounts()
        table_row = TableRow(driver=accounts_page.driver, label=account_name)
        table_row.check()
        confirm_panel = accounts_page.delete_account_button.click()
        confirm_panel.click(label='Delete')
        table_row.wait_until_condition(condition=EC.staleness_of, timeout=3)
        Filter(driver=accounts_page.driver).write(account_name)
        with pytest.raises(NoSuchElementException):
            table_row.get_element(reload=True)

    def test_create_account_check_required_fields(self):
        accounts_page = self.admin_dashboard.go_to_accounts()
        account_edit_popup = accounts_page.new_account_click()
        account_edit_popup.create_button.click()
        for required_field in account_edit_popup.required_fields:
            class_attr = required_field.get_element().get_attribute('class')
            assert 'x-form-invalid-field' in class_attr.split()
