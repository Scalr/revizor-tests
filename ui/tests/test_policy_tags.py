import pytest
import re
import os
import base64
import time

from selenium.common.exceptions import NoSuchElementException

from revizor2.conf import CONF
from pages.login import LoginPage
from pages.admin_scope import PolicyTags
from elements import locators
from elements.base import Label, Button

DEFAULT_USER = CONF.credentials.testenv.accounts.admin['username']
DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.admin['password']


class TestPolicyTags:

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        self.driver.implicitly_wait(10)
        self.container = testenv
        self.url = 'http://%s.test-env.scalr.com' % self.container.te_id
        login_page = LoginPage(
            self.driver,
            self.url).open()
        self.admin_dashboard = login_page.login(DEFAULT_USER, DEFAULT_PASSWORD, admin=True)

    def goto_policy_tag_page(self):
        self.admin_dashboard.scalr_main_menu.click()
        main_menu_items = self.admin_dashboard.scalr_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_tag_page = self.admin_dashboard.menu.go_to_admin().menu.go_to_policy_tags()
        return policy_tag_page

    def test_cancel_create_policy_tag(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.cancel_button.click()
        assert policy_tag_page.name_field.hidden(), 'Name field is present in Create Policy Tags submenu!'
        assert policy_tag_page.save_button.hidden(), 'Save button is present in Create Policy Tags submenu!'
        assert policy_tag_page.cancel_button.hidden(), 'Cancel button is present in Create Policy Tags submenu!'

    def test_create_new_policy_tag(self, tag_name='tag1', aserts=True):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.name_field.write(tag_name)
        policy_tag_page.save_button.click()
        time.sleep(2)
        if aserts:
            assert policy_tag_page.page_message.text == "Policy Tag successfully saved", \
                "No message present about successful saving of the new Policy Tag"
            assert policy_tag_page.created_tag(tag_name).visible(), "Policy Tag was not found!"
        return policy_tag_page

    def test_create_tag_with_empty_field(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.save_button.click()
        assert policy_tag_page.input_alert(text='This field is required'), "Alert message was not found!"

    def test_create_tag_with_invalid_name(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        tag_names = ['!#$%&()*+,-./:;<=>?@[\]^_`{|}~', 'qw', 'QWER', '-qwer', 'qwer-', ',qwer', 'qwer,']
        for tag_name in tag_names:
            policy_tag_page.name_field.write(tag_name)
            policy_tag_page.save_button.click()
            assert policy_tag_page.input_alert(
                'Invalid name. Tag name should contain only lowercase letters,'
                ' numbers and dashes, started and finished with letter or numeral. Length from 3 to 10 chars.'),\
                "Alert message was not found!"

    def test_create_tag_with_duplicate_name(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        for _ in range(2):
            policy_tag_page.new_policy_tag_button.click()
            policy_tag_page.name_field.write('qwerty')
            policy_tag_page.save_button.click()
            time.sleep(1)
        assert policy_tag_page.input_alert(
            text='Name is in use'), "Alert message was not found!"

    def test_cancel_deletion_policy_tag(self, tag_name='tag2'):
        policy_tag_page = TestPolicyTags.test_create_new_policy_tag(self, tag_name)
        policy_tag_page.created_tag(tag_name).click()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Cancel')
        time.sleep(2)
        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.created_tag(tag_name).visible(), "Policy Tag was not found!"

    def test_delete_policy_tag(self, tag_name='tag3'):
        policy_tag_page = TestPolicyTags.test_create_new_policy_tag(self, tag_name)
        policy_tag_page.created_tag(tag_name).click()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Delete')
        time.sleep(2)
        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.page_message.text == "Policy Tag successfully deleted", \
            "No message present about successful deletion of the Policy Tag"
        assert policy_tag_page.created_tag(tag_name).hidden(), " The Policy Tag was not deleted!"
