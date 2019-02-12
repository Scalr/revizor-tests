import pytest
import re
import os
import base64
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from revizor2.conf import CONF
from pages.login import LoginPage
from pages.roles import RolesEdit
from pages.global_scope import PolicyTags
from elements import locators
from elements.base import Label, Button, Table

DEFAULT_USER = CONF.credentials.testenv.accounts.admin['username']
DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.admin['password']


class TestPolicyTags:

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        self.driver.implicitly_wait(10)
        self.container = testenv
        self.url = 'http://%s.test-env.scalr.com' % self.container.te_id
        login_page = LoginPage(self.driver, self.url).open()
        self.dashboard = login_page.login(DEFAULT_USER, DEFAULT_PASSWORD)

# Admin scope> Policy tags> Create, validate and delete

    def goto_policy_tag_page(self):
        self.dashboard.scalr_main_menu.click()
        main_menu_items = self.dashboard.scalr_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_tag_page = self.dashboard.menu.go_to_admin().menu.go_to_policy_tags()
        return policy_tag_page

    def test_cancel_create_policy_tag(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.cancel_button.click()
        assert policy_tag_page.name_field.hidden(), 'Name field is present in Create Policy Tags submenu!'
        assert policy_tag_page.save_button.hidden(), 'Save button is present in Create Policy Tags submenu!'
        assert policy_tag_page.cancel_button.hidden(), 'Cancel button is present in Create Policy Tags submenu!'

    def test_create_new_policy_tag(self, tag_names=['test1'], aserts=True):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        for name in tag_names:
            policy_tag_page.new_policy_tag_button.click()
            policy_tag_page.name_field.write(name)
            policy_tag_page.save_button.click()
            time.sleep(2)
            if aserts:
                assert policy_tag_page.page_message.text == "Policy Tag successfully saved", \
                    "No message present about successful saving of the new Policy Tag"
                assert policy_tag_page.created_tag(name).visible(), "Policy Tag was not found!"
        time.sleep(2)
        return policy_tag_page

    def test_create_tag_with_empty_field(self):
        policy_tag_page = TestPolicyTags.goto_policy_tag_page(self)
        policy_tag_page.new_policy_tag_button.click()
        policy_tag_page.save_button.click()
        assert policy_tag_page.input_alert(
            text='This field is required'), "Alert message was not found!"

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
            policy_tag_page.name_field.write('test2')
            policy_tag_page.save_button.click()
            time.sleep(1)
        assert policy_tag_page.input_alert(
            text='Name is in use'), "Alert message was not found!"

    def test_cancel_deletion_policy_tag(self, name='test3'):
        policy_tag_page = TestPolicyTags.test_create_new_policy_tag(self, tag_names=[name])
        policy_tag_page.created_tag(name).click()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Cancel')
        time.sleep(2)
        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.created_tag(name).visible(), "Policy Tag was not found!"

    def test_delete_policy_tag(self, name='test4'):
        policy_tag_page = TestPolicyTags.test_create_new_policy_tag(self, tag_names=[name])
        policy_tag_page.created_tag(name).click()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Delete')
        time.sleep(2)
        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.page_message.text == "Policy Tag successfully deleted", \
            "No message present about successful deletion of the Policy Tag"
        assert policy_tag_page.created_tag(name).hidden(), "The Policy Tag was not deleted!"

# Policy tags> Roles application

    def preparationg_applying_to_roles(self):
        tag_names = ['tag-1', 'tag-2', 'tag-3']
        TestPolicyTags.test_create_new_policy_tag(self, tag_names)

    def scope_switch(self, scope):
        """
        :param scope: can be 'default' - Environment
         or 'admin' - Global scope
        """
        self.dashboard.menu.logout()
        global DEFAULT_USER
        global DEFAULT_PASSWORD
        if scope == 'default':
            DEFAULT_USER = CONF.credentials.testenv.accounts.default['username']
            DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.default['password']
        elif scope == 'admin':
            DEFAULT_USER = CONF.credentials.testenv.accounts.admin['username']
            DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.admin['password']
        login_page = LoginPage(self.driver, self.url).open()
        self.dashboard = login_page.login(DEFAULT_USER, DEFAULT_PASSWORD)

    def go_to_roles_page_account_scope(self):
        account_dashboard = self.dashboard.menu.go_to_account()
        account_dashboard.scalr_main_menu.click()
        main_menu_items = account_dashboard.scalr_main_menu.list_items()
        main_menu_items['Roles\nADD NEW'].mouse_over()
        roles_page = account_dashboard.go_to_roles()
        return roles_page

    def test_create_role_with_policy_tag_admin_scope(self):
        TestPolicyTags.preparationg_applying_to_roles(self)
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role()
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1')
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def create_role_with_policy_tag_account_scope(self):
        TestPolicyTags.scope_switch(self, scope='default')
        roles_page = TestPolicyTags.go_to_roles_page_account_scope(self)
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-with-tag-acc'
        }
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1', **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"
        return roles_page

    def test_validation_add_second_policy_tag_to_role(self):
        role_name = 'selenium-ubuntu1404-with-tag-acc'
        roles_page = TestPolicyTags.create_role_with_policy_tag_account_scope(self)
        roles_page.search_role_field.write(role_name)
        RolesEdit.created_role(self, role_name).click()
        roles_page.roles_edit_button.click()
        time.sleep(10)
        RolesEdit.tags_input_field.click()
        Button(xpath="//li[contains(.,'tag-3')]", driver=self.driver).click()
        assert RolesEdit.tooltip_one_policy_allowed.visible(), "Tooltip message was not found!"

    def search_field_trigger(self, roles_page, tag_name, *roles_names):
        roles_page.searchfield_trigger_menu.click()
        roles_page.searchfield_trigger_tag_list.click()
        roles_page.searchfield_trigger_find_tag(tag_name).click()
        roles_page.body_container.click()
        assert roles_page.roles_table_sorted_by_tag(tag_name).visible(), "The roles table is not sorted by Tag!"
        for name in roles_names:
            role = Table(text=name, driver=self.driver)
            assert role.visible(), "Role was not found!"

    def test_search_field_trigger_acc(self):
        roles_page = TestPolicyTags.go_to_roles_page_account_scope(self)
        tag_name = 'tag-1'
        roles_names = ('selenium-ubuntu1404-with-tag-admin', 'selenium-ubuntu1404-with-tag-acc')
        TestPolicyTags.search_field_trigger(self, roles_page, tag_name, *roles_names)

    def test_policy_tag_cannot_be_used_as_script_tag(self):
        scripts_page = self.dashboard.menu.go_to_account().go_to_scripts()
        time.sleep(1)
        scripts_page.new_script_button.click()
        scripts_page.script_name_field.write('policy_tag_cannot_be_used_as_script_tag')
        scripts_page.script_content_field_activation.click()
        scripts_page.script_content_field.write_to_hidden('#!/bin/bash')
        scripts_page.tags_field.write('tag-1')
        scripts_page.tags_field.write_to_hidden(Keys.ENTER)
        scripts_page.save_button.click()
        scripts_page.save_button.click()
        assert scripts_page.tooltip_policy_tag_not_allowed.visible(), "Tooltip message was not found!"

    def test_create_role_with_policy_tag_env_scope(self):
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role(env=True)
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-with-tag-env'
        }
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1', **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def test_search_field_trigger_env(self):
        roles_page = self.dashboard.menu.go_to_roles()
        roles_names = (
            'selenium-ubuntu1404-with-tag-admin',
            'selenium-ubuntu1404-with-tag-acc',
            'selenium-ubuntu1404-with-tag-env')
        tag_name = 'tag-1'
        TestPolicyTags.search_field_trigger(self, roles_page, tag_name, *roles_names)

# Policy tags> Application in Policy

    def test_preparationg_applying_in_policy(self):
        TestPolicyTags.scope_switch(self, scope='admin')
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-admin'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

        TestPolicyTags.scope_switch(self, scope='default')
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role(env=True)
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-env'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

        roles_page = TestPolicyTags.go_to_roles_page_account_scope(self)
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-acc'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def go_to_policyengine_groups(self):
        account_dashboard = self.dashboard.menu.go_to_account()
        account_dashboard.scalr_main_menu.click()
        main_menu_items = account_dashboard.scalr_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_groups_page = account_dashboard.go_to_policy_groups()
        return policy_groups_page

    def test_chef_servers_config_with_policy(self):
        policy_groups_page = TestPolicyTags.go_to_policyengine_groups(self)
        time.sleep(2)
        policy_groups_page.new_policy_group_button.click()
        policy_groups_page.name_field.write('selenium-policy-group-1')
        policy_groups_page.group_type_combobox.select('Configuration')
        policy_groups_page.new_policy_button.click()
        policy_groups_page.policy_type_combobox.select('chef.servers')
        policy_groups_page.role_tag_combobox.select('tag-1')
        policy_groups_page.chef_servers_checkbox.click()
        policy_groups_page.new_policy_ok_button.click()
        policy_groups_page.save_button.click()
        assert policy_groups_page.tooltip_policy_group_saved.visible(), \
            "Tooltip message about successfully saved Policy Group was not found!"

    def test_add_config_to_environment(self):
        env_page = self.dashboard.menu.go_to_account().menu.go_to_environments()
        env_page.select_environment(' acc1env1')
        env_page.policies_tab.click()
        env_page.link_cloud_to_environment('Configuration','selenium-policy-group-1')
        env_page.save_button.click()
        assert env_page.page_message.text == "Environment saved", \
            "No message present about successfull saving of the new Environment"
        assert env_page.linked_policy_group("selenium-policy-group-1").visible()

    @pytest.mark.skip('SCALRCORE-11738')
    def test_check_application_with_policy_tag_role(self):
        TestPolicyTags.scope_switch(self, scope='default')

        farms_page = self.dashboard.menu.go_to_environment(
            env_name=" acc1env1").menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Farm1')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        category = 'Base'
        roles_without_tag = ['selenium-ubuntu1404-admin',
                             'selenium-ubuntu1404-env',
                             'selenium-ubuntu1404-acc']
        new_farm_page.add_farm_role_button.click()
        for role_name in roles_without_tag:
            new_farm_page.add_farm_role(category, role_name)
            new_farm_page.add_role_to_farm_button.click()
        # Blocked by SCALRCORE-11738
