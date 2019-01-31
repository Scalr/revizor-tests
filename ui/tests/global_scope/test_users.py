# coding: utf-8
"""
Created on 01.11.18
@author: Eugeny Kurkovich
"""
import pytest

from uuid import uuid4

from revizor2.conf import CONF
from pages.login import LoginPage
from elements.base import TableRow

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER = CONF.credentials.testenv.accounts.admin['username']
PASSWORD = CONF.credentials.testenv.accounts.admin['password']


class TestUsers(object):

    test_user_full_name = "Selenium User"
    test_user_email = f"selenium-{uuid4().hex[0:8]}@localhost.net"

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, request, testenv):
        load_timeout = request.config.getoption("load_timeout")
        self.driver = selenium
        self.driver.implicitly_wait(10)
        login_page = LoginPage(
            self.driver,
            f'http://{testenv.te_id}.test-env.scalr.com',
            timeout=load_timeout
        ).open()
        self.admin_dashboard = login_page.login(USER, PASSWORD)

    def test_create_user(self):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.full_name_field.write(self.test_user_full_name)
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.generate_password_button.check()
        new_user_panel.change_password_at_signin_button.check()
        new_user_panel.set_suspended_button.click()
        new_user_panel.comments_field.write(f'suspended user: {self.test_user_full_name}')
        new_user_panel.set_global_admin_perm_button.check()
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(EC.invisibility_of_element_located, timeout=3)
        password_details_panel.click_by_label('Close')
        assert TableRow(driver=users_page.driver, label=self.test_user_email).exists

    def test_activate_ceated_user(self):
        users_page = self.admin_dashboard.go_to_users()
        inactive_user = TableRow(driver=users_page.driver, label=self.test_user_email)
        inactive_user.check()
        acivate_user_confirm_panel = users_page.set_activate_button.click()
        acivate_user_confirm_panel.click_by_label('OK')

    def test_create_duplicate_user(self):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.save_button.click(panel_type='form')
        wait = WebDriverWait(new_user_panel.driver, 3)
        wait.until(EC.presence_of_element_located((By.XPATH, "//* [text()='User already exists']")))
        assert 'x-form-invalid-field' in new_user_panel.email_field.get_element().get_attribute('class').split()



