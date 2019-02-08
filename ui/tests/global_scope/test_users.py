# coding: utf-8
"""
Created on 01.11.18
@author: Eugeny Kurkovich
"""
import pytest

from uuid import uuid4

from pages.login import LoginPage
from elements import locators
from elements.base import TableRow, Filter
from elements.page_objects import ConfirmPanel
from utils.custom_waits import element_class_value_no_presence_of

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestUsers(object):

    test_user_full_name = "Selenium User"

    required_fields_args = [
        ("email_field", "test@scalr.com", "User already exists"),
        ("email_field", "invalid value", "field should be an e-mail address"),
        ("password_field", "invalid password", "Password doesn\'t contain any characters"),
        ("password_field", "", "This field is required"),
        ("password_field", "not confirmed password", "Passwords do not match")]

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, request, testenv):
        load_timeout = request.config.getoption("load_timeout")
        self.driver = selenium
        self.driver.implicitly_wait(10)
        login_page = LoginPage(
            self.driver,
            f'https://{testenv.te_id}.test-env.scalr.com',
            timeout=load_timeout
        ).open()
        self.admin_dashboard = login_page.login(
            request.config.admin_login,
            request.config.admin_pass)
        self.test_user_email = f"selenium-{uuid4().hex[0:8]}@localhost.net"

    def test_create_user(self):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.full_name_field.write(self.test_user_full_name)
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.generate_password_button.check()
        new_user_panel.change_password_at_signin_button.check()
        new_user_panel.comments_field.write(f'Selenium user: {self.test_user_full_name}')
        new_user_panel.set_global_admin_perm_button.check()
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(
            EC.staleness_of, timeout=3)
        password_details_panel.click(label='Close')
        users_page.refresh_button.wait_until_condition(EC.element_to_be_clickable)
        users_page.refresh_button.click()
        Filter(driver=users_page.driver).write(self.test_user_email)
        assert TableRow(driver=users_page.driver, label=self.test_user_email).exists

    def test_activate_suspended_user(self):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.set_suspended_button.click()
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(
            EC.staleness_of, timeout=3)
        password_details_panel.click(label='Close')
        users_page.refresh_button.wait_until_condition(EC.element_to_be_clickable)
        users_page.refresh_button.click()
        Filter(driver=users_page.driver).write(self.test_user_email)
        user_row = TableRow(driver=users_page.driver, label=self.test_user_email)
        user_row.check()
        acivate_confirm_panel = users_page.set_activate_button.click()
        acivate_confirm_panel.click(label='OK')
        is_active = ''.join((user_row.locator[1], "/descendant::* [text()='Active']"))
        WebDriverWait(users_page.driver, 3).until(
            EC.presence_of_element_located(locators.XpathLocator(is_active)))

    def test_delete_user(self):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.email_field.write(self.test_user_email)
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(
            EC.staleness_of, timeout=3)
        password_details_panel.click(label='Close')
        users_page.refresh_button.wait_until_condition(EC.element_to_be_clickable)
        users_page.refresh_button.click()
        Filter(driver=users_page.driver).write(self.test_user_email)
        user_row = TableRow(driver=users_page.driver, label=self.test_user_email)
        user_row.check()
        confirm_panel = users_page.delete_user_button.click()
        confirm_panel.click(label='Delete')
        hint_locator = locators.XpathLocator(
            "//* [text()='User successfully deleted.']"
            "/following::img [contains(@class, 'x-tool-close-white')]")
        WebDriverWait(users_page.driver, 3).until(EC.presence_of_element_located(hint_locator)).click()
        users_page.refresh_button.click()
        with pytest.raises(NoSuchElementException):
            user_row.get_element(reload=True)

    def test_change_auto_gen_password(self, request):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.generate_password_button.check()
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(EC.staleness_of, timeout=3)
        password_details_panel.click(hint="Show password")
        password_field = password_details_panel.find_descendant_element("input")
        password = password_field.get_attribute('value')
        new_password = 2*password
        password_details_panel.click(label='Close')
        users_page.refresh_button.wait_until_condition(EC.element_to_be_clickable)
        users_page.refresh_button.click()
        edit_user_panel = users_page.edit_user(self.test_user_email)
        password_change_panel = edit_user_panel.change_user_password_button.click(panel_type='form')
        edit_user_panel.change_user_password_button.wait_until_condition(EC.staleness_of, timeout=3)
        password_change_panel.click(label='Automatically generate a password')
        password_change_panel.find_descendant_element("input [@name='password']").send_keys(new_password)
        password_change_panel.find_descendant_element("input [@name='cpassword']").send_keys(new_password)
        password_change_panel.click(label="Change password")
        admin_password_panel = ConfirmPanel(driver=users_page.driver)
        admin_password_panel.find_descendant_element(
            "input [@name='currentPassword']").send_keys(request.config.admin_pass)
        # waiting for button click availability
        WebDriverWait(users_page.driver, 3).until(
            element_class_value_no_presence_of(
                admin_password_panel.find_descendant_element("* [text()='OK']/ancestor::a[1]"),
                'x-btn-disabled'))
        admin_password_panel.click(label='OK')
        WebDriverWait(users_page.driver, 3).until(
            EC.presence_of_element_located(
                locators.XpathLocator("//* [text()='Password successfully updated']")))
        password_panel = ConfirmPanel(driver=users_page.driver, panel_type='form')
        password_panel.click(hint="Show password")
        password_field = password_panel.find_descendant_element("input")
        assert new_password == password_field.get_attribute('value')
        password_panel.click(label='Close')
        edit_user_panel.cancel_button.click()
        assert TableRow(driver=users_page.driver, label=self.test_user_email).exists

    @pytest.mark.parametrize("field_name, field_value, alert_hint", required_fields_args)
    def test_check_required_fields_validation(self, field_name, field_value, alert_hint):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        if 'password' in field_name:
            new_user_panel.generate_password_button.uncheck()
        getattr(new_user_panel, field_name).write(field_value or '')
        new_user_panel.save_button.click(panel_type='form')
        alert_hint = locators.XpathLocator(f'//div [@role="alert"]//descendant::*[contains(text(), "{alert_hint}")]')
        WebDriverWait(new_user_panel.driver, 3).until(EC.presence_of_element_located(alert_hint))
        alert_attrs = getattr(new_user_panel, field_name).get_element().get_attribute('class')
        assert 'x-form-invalid-field' in alert_attrs.split()
