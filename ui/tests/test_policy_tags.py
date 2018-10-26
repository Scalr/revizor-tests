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

    def test_create_new_policy_tag(self):
        self.admin_dashboard.scalr_main_menu.click()
        main_menu_items = self.admin_dashboard.scalr_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_tag_page = self.admin_dashboard.menu.go_to_admin().menu.go_to_policy_tags()

        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.name_field.write('tag1')
        policy_tag_page.save_button.click()
        assert policy_tag_page.page_message.text == "Policy Tag successfully saved", \
            "No message present about successfull saving of the new Policy Tag"


