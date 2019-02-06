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
    test_user_email = f"selenium-{uuid4().hex[0:8]}@localhost.net"

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

    def _check_required_fields_validation(self, field_name, field_value, alert_hint):
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

    def test_create_suspended_user(self):
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
        new_user_panel.save_button.wait_until_condition(
            EC.staleness_of, timeout=3)
        password_details_panel.click_by_label('Close')
        Filter(driver=users_page.driver).write(self.test_user_email)
        assert TableRow(driver=users_page.driver, label=self.test_user_email).exists

    def test_activate_user(self):
        users_page = self.admin_dashboard.go_to_users()
        Filter(driver=users_page.driver).write(self.test_user_email)
        inactive_user = TableRow(driver=users_page.driver, label=self.test_user_email)
        inactive_user.check()
        acivate_user_confirm_panel = users_page.set_activate_button.click()
        acivate_user_confirm_panel.click_by_label('OK')

    def test_delete_user(self):
        users_page = self.admin_dashboard.go_to_users()
        Filter(driver=users_page.driver).write(self.test_user_email)
        user_row = TableRow(driver=users_page.driver, label=self.test_user_email)
        user_row.check()
        confirm_panel = users_page.delete_user_button.click()
        confirm_panel.click_by_label('Delete')
        confirm_panel.wait_presence_off()
        user_row.wait_until_condition(condition=EC.staleness_of, timeout=3)
        with pytest.raises(NoSuchElementException):
            user_row.get_element(reload=True)

    def test_change_auto_gen_password(self, request):
        users_page = self.admin_dashboard.go_to_users()
        new_user_panel = users_page.new_user_click()
        new_user_panel.email_field.write(self.test_user_email)
        new_user_panel.generate_password_button.check()
        password_details_panel = new_user_panel.save_button.click(panel_type='form')
        new_user_panel.save_button.wait_until_condition(EC.staleness_of, timeout=3)
        password_details_panel.click_by_hint("Show password")
        password_field = password_details_panel.find_descendant_element("input")
        password = password_field.get_attribute('value')
        new_password = 2*password
        password_details_panel.click_by_label('Close')
        password_details_panel.wait_presence_off()
        edit_user_panel = users_page.edit_user(self.test_user_email)
        password_change_panel = edit_user_panel.change_user_password_button.click(panel_type='form')
        edit_user_panel.change_user_password_button.wait_until_condition(EC.staleness_of, timeout=3)
        password_change_panel.click_by_label('Automatically generate a password')
        password_change_panel.find_descendant_element("input [@name='password']").send_keys(new_password)
        password_change_panel.find_descendant_element("input [@name='cpassword']").send_keys(new_password)
        password_change_panel.click_by_label("Change password")
        password_change_panel.wait_presence_off()
        admin_password_panel = ConfirmPanel(driver=users_page.driver)
        admin_password_panel.find_descendant_element(
            "input [@name='currentPassword']").send_keys(request.config.admin_pass)
        # waiting for button click availability
        WebDriverWait(users_page.driver, 3).until(
            element_class_value_no_presence_of(
                admin_password_panel.find_descendant_element("* [text()='OK']/ancestor::a[1]"),
                'x-btn-disabled'))
        admin_password_panel.click_by_label('OK')
        WebDriverWait(users_page.driver, 3).until(
            EC.presence_of_element_located(
                locators.XpathLocator("//* [text()='Password successfully updated']")))
        password_panel = ConfirmPanel(driver=users_page.driver, panel_type='form')
        password_panel.click_by_hint("Show password")
        password_field = password_panel.find_descendant_element("input")
        assert new_password == password_field.get_attribute('value')
        password_panel.click_by_label('Close')
        password_panel.wait_presence_off()
        edit_user_panel.cancel_button.click()
        assert TableRow(driver=users_page.driver, label=self.test_user_email).exists

    def test_create_duplicate_user(self):
        self._check_required_fields_validation(
            field_name="email_field",
            field_value=self.test_user_email,
            alert_hint="User already exists")

    def test_pass_invalid_email_value(self):
        self._check_required_fields_validation(
            field_name="email_field",
            field_value="invalid value",
            alert_hint="field should be an e-mail address"
        )

    def test_pass_invalid_password(self):
        self._check_required_fields_validation(
            field_name="password_field",
            field_value="invalid password",
            alert_hint="Password doesn\'t contain any characters"
        )

    def test_pass_empty_password(self):
        self._check_required_fields_validation(
            field_name="password_field",
            field_value="",
            alert_hint="This field is required"
        )

    def test_not_confirmed_password(self):
        self._check_required_fields_validation(
            field_name="confirm_password_field",
            field_value="not confirmed password",
            alert_hint="Passwords do not match"
        )

