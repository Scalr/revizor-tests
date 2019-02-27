import pytest

from selenium.webdriver.common.keys import Keys

from revizor2.conf import CONF
from pages.login import LoginPage
from pages.roles import RolesEdit
from elements.base import TableRow

from selenium.webdriver.support import expected_conditions as EC

DEFAULT_USER = CONF.credentials.testenv.accounts.super_admin['username']
DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.super_admin['password']


class TestPolicyTags:

    roles_without_tag = ['selenium-ubuntu1404-admin',
                         'selenium-ubuntu1404-acc',
                         'selenium-ubuntu1404-env']
    roles_with_tag = ['selenium-ubuntu1404-with-tag-admin',
                      'selenium-ubuntu1404-with-tag-acc',
                      'selenium-ubuntu1404-with-tag-env']

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        login_page = LoginPage(
            self.driver,
            'http://%s.test-env.scalr.com' % testenv.te_id).open()
        self.dashboard = login_page.login(DEFAULT_USER, DEFAULT_PASSWORD)

    def go_to_acc_scope(self, switch_to_env=False):
        """
        Default: Switches to Account level Dashboard.
        Returns AccountDashboard page object
        if param: switch_to_env=True:
        Switches to Environments page level Dashboard.
        Returns EnvironmentDashboard page object
        """
        acc = self.dashboard.go_to_accounts().go_to_account()
        if switch_to_env:
            env = acc.menu.change_environment(env_name="acc1env1")
            return env
        return acc

    def preparationg_applying_to_roles(self):
        tag_names = 'tag-1', 'tag-2', 'tag-3'
        policy_tag_page = self.create_new_policy_tag(*tag_names)
        for name in tag_names:
            assert policy_tag_page.created_tag(name).visible(), "Policy Tag was not found!"

    def goto_policy_tag_page(self):
        """
        :return: Policy Tag page (Global Scope).
        """
        self.dashboard.scope_main_menu.click()
        main_menu_items = self.dashboard.scope_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_tag_page = self.dashboard.menu.go_to_admin().menu.go_to_policy_tags()
        return policy_tag_page

    def go_to_roles_page_account_scope(self, account_dashboard):
        account_dashboard.scope_main_menu.click()
        main_menu_items = account_dashboard.scope_main_menu.list_items()
        main_menu_items['Roles\nADD NEW'].mouse_over()
        roles_page = account_dashboard.go_to_roles()
        return roles_page

    def go_to_policyengine_groups(self):
        account_dashboard = self.go_to_acc_scope()
        account_dashboard.scope_main_menu.click()
        main_menu_items = account_dashboard.scope_main_menu.list_items()
        main_menu_items['Policy Engine'].mouse_over()
        policy_groups_page = account_dashboard.go_to_policy_groups()
        return policy_groups_page

    def create_new_policy_tag(self, *tag_names, aserts=True):
        policy_tag_page = self.goto_policy_tag_page()
        for name in tag_names:
            policy_tag_page.new_policy_tag_button().click()
            policy_tag_page.name_field.write(name)
            policy_tag_page.save_button.click()
            if aserts:
                assert policy_tag_page.page_message.text == "Policy Tag successfully saved", \
                    "No message present about successful saving of the new Policy Tag"
                policy_tag_page.created_tag(name).wait_until_condition(EC.staleness_of, timeout=2)
        return policy_tag_page

    def search_field_trigger(self, roles_page, tag_name):
        """
        Used by acc & env scopes.
        """
        roles_page.searchfield_trigger_menu.click()
        roles_page.searchfield_trigger_tag_list.click()
        roles_page.searchfield_trigger_find_tag(tag_name).click()
        roles_page.body_container.click()
        roles_page.roles_table_sorted_by_tag(tag_name).wait_until_condition(
            EC.visibility_of_element_located)
        assert roles_page.roles_table_sorted_by_tag(tag_name).visible(), "The roles table is not sorted by Tag!"

# Admin scope> Policy tags> Create, validate and delete

    def test_cancel_create_policy_tag(self):
        policy_tag_page = self.goto_policy_tag_page()
        policy_tag_page.new_policy_tag_button().click()
        policy_tag_page.cancel_button.click()
        assert policy_tag_page.name_field.hidden(), 'Name field is present in Create Policy Tags submenu!'
        assert policy_tag_page.save_button.hidden(), 'Save button is present in Create Policy Tags submenu!'
        assert policy_tag_page.cancel_button.hidden(), 'Cancel button is present in Create Policy Tags submenu!'

    def test_create_new_policy_tag(self):
        tag_names = 'test1',
        create_tag = self.create_new_policy_tag(*tag_names)
        assert create_tag.created_tag(tag_names).visible(), "Policy Tag was not found!"

    def test_create_tag_with_empty_field(self):
        policy_tag_page = self.goto_policy_tag_page()
        policy_tag_page.new_policy_tag_button().click()
        policy_tag_page.save_button.click()
        assert policy_tag_page.alert_visible(
            text='This field is required'), "Alert message was not found!"

    def test_create_tag_with_invalid_name(self):
        invalid_tag_names = [
            '!#$%&()*+,-./:;<=>?@[\]^_`{|}~', 'qw',
            'QWER', '-qwer', 'qwer-', ',qwer', 'qwer,']
        policy_tag_page = self.goto_policy_tag_page()
        policy_tag_page.new_policy_tag_button().click()
        for name in invalid_tag_names:
            policy_tag_page.name_field.write(name)
            policy_tag_page.save_button.click()
            assert policy_tag_page.alert_visible(
                'Invalid name. Tag name should contain only lowercase letters,'
                ' numbers and dashes, started and finished with letter or numeral. Length from 3 to 10 chars.'),\
                "Alert message was not found!"

    def test_create_tag_with_duplicate_name(self):
        policy_tag_page = self.goto_policy_tag_page()
        for _ in range(2):
            policy_tag_page.new_policy_tag_button().click()
            policy_tag_page.name_field.write('test2')
            policy_tag_page.save_button.click()
        assert policy_tag_page.alert_visible(
            text='Name is in use'), "Alert message was not found!"

    def test_cancel_deletion_policy_tag(self):
        tag_names = 'test3',
        policy_tag_page = self.create_new_policy_tag(*tag_names)
        assert policy_tag_page.created_tag(tag_names).visible(), "Policy Tag was not found!"
        policy_tag_page.created_tag(tag_names).select()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Cancel')
        policy_tag_page.created_tag(tag_names).wait_until_condition(EC.staleness_of, timeout=2)
        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.created_tag(tag_names).visible(), "Policy Tag was not found!"

    def test_delete_policy_tag(self):
        tag_names = 'test44',
        policy_tag_page = self.create_new_policy_tag(*tag_names)
        assert policy_tag_page.created_tag(tag_names).visible(), "Policy Tag was not found!"
        policy_tag_page.created_tag(tag_names).select()
        policy_tag_page.delete_button_before_pop_up.click()
        policy_tag_page.deletion_pop_up_buttons('Delete')

        assert policy_tag_page.deletion_pop_up.hidden(), "The confirmation pop-up was not closed!"
        assert policy_tag_page.deletion_message.visible, \
            "No message present about successful deletion of the Policy Tag"
        assert policy_tag_page.created_tag(tag_names).hidden(), "The Policy Tag was not deleted!"

# Policy tags> Roles application

    def test_create_role_with_policy_tag_admin_scope(self):
        self.preparationg_applying_to_roles()
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role()
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1')
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def test_create_role_with_policy_tag_account_scope(self):
        account_dashboard = self.go_to_acc_scope()
        roles_page = self.go_to_roles_page_account_scope(account_dashboard)
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-with-tag-acc'
        }
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1', **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"
        return roles_page

    def test_validation_add_second_policy_tag_to_role(self):
        role_name = 'selenium-ubuntu1404-with-tag-acc'
        account_dashboard = self.go_to_acc_scope()
        roles_page = self.go_to_roles_page_account_scope(account_dashboard)
        roles_page.search_role_field.write(role_name)
        RolesEdit.created_role(self, role_name).select()
        edit_role_page = roles_page.edit_role()
        edit_role_page.add_tag_to_role('tag-3')
        assert edit_role_page.tooltip_one_policy_allowed.visible(), "Tooltip message was not found!"

    def test_search_field_trigger_acc(self):
        roles_names = ('selenium-ubuntu1404-with-tag-admin', 'selenium-ubuntu1404-with-tag-acc')
        account_dashboard = self.go_to_acc_scope()
        roles_page = self.go_to_roles_page_account_scope(account_dashboard)
        tag_name = 'tag-1'
        self.search_field_trigger(roles_page, tag_name)
        for name in roles_names:
            role = TableRow(text=name, driver=self.driver)
            assert role.visible(), "Role was not found!"

    def test_policy_tag_cannot_be_used_as_script_tag(self):
        acc_dashboard = self.go_to_acc_scope()
        scripts_page = acc_dashboard.go_to_scripts()
        scripts_page.new_script_button.wait_until_condition(EC.staleness_of, timeout=2)
        scripts_page.new_script_button.click()
        scripts_page.script_name_field.wait_until_condition(EC.staleness_of, timeout=2)
        scripts_page.script_name_field.write('policy_tag_cannot_be_used_as_script_tag')
        scripts_page.script_content_field_activation.click()
        scripts_page.script_content_field.write('#!/bin/bash', hidden=True, clear=False)
        scripts_page.tags_field.write('tag-1')
        scripts_page.tags_field.write(Keys.ENTER, hidden=True, clear=False)
        scripts_page.body_container.click()
        scripts_page.save_button.click()
        scripts_page.tooltip_policy_tag_not_allowed.wait_until_condition(EC.visibility_of_element_located)
        assert scripts_page.tooltip_policy_tag_not_allowed.visible(), "Tooltip message was not found!"

    def test_create_role_with_policy_tag_env_scope(self):
        env_dashboard = self.go_to_acc_scope(switch_to_env=True)
        roles_page = env_dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role(env=True)
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-with-tag-env'
        }
        RolesEdit.create_role(self, roles_edit_page, tag_name='tag-1', **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def test_search_field_trigger_env(self):
        env_dashboard = self.go_to_acc_scope(switch_to_env=True)
        roles_page = env_dashboard.menu.go_to_roles()
        roles_names = tuple(self.roles_with_tag)
        tag_name = 'tag-1'
        self.search_field_trigger(roles_page, tag_name)
        for name in roles_names:
            role = TableRow(text=name, driver=self.driver)
            assert role.visible(), "Role was not found!"

# Policy tags> Application in Policy

    def test_preparationg_applying_in_policy(self):
        roles_page = self.dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-admin'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

        account_dashboard = self.go_to_acc_scope()
        roles_page = self.go_to_roles_page_account_scope(account_dashboard)
        roles_edit_page = roles_page.new_role()
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-acc'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

        env_dashboard = account_dashboard.menu.change_environment(env_name="acc1env1")
        roles_page = env_dashboard.menu.go_to_roles()
        roles_edit_page = roles_page.new_role(env=True)
        roles_settings = {
            'role_name': 'selenium-ubuntu1404-env'
        }
        RolesEdit.create_role(self, roles_edit_page, **roles_settings)
        assert roles_page.new_role_button.visible(), "We did not go to the Roles page"

    def test_chef_servers_config_with_policy(self):
        policy_groups_page = self.go_to_policyengine_groups()
        policy_groups_page.new_policy_group_button.wait_until_condition(EC.staleness_of, timeout=2)
        policy_groups_page.new_policy_group_button.click()
        policy_groups_page.name_field.write('selenium-policy-group-1')
        policy_groups_page.group_type_combobox.select('Configuration')
        policy_groups_page.new_policy_button.click()
        policy_groups_page.policy_type_combobox.select('chef.servers')
        policy_groups_page.role_tag_combobox.select('tag-1')
        policy_groups_page.chef_servers_checkbox.click()
        policy_groups_page.new_policy_ok_button.click()
        policy_groups_page.save_button.click()
        policy_groups_page.tooltip_policy_group_saved.wait_until_condition(
            EC.visibility_of_element_located)
        assert policy_groups_page.tooltip_policy_group_saved.visible(), \
            "Tooltip message about successfully saved Policy Group was not found!"

    def test_add_config_to_environment(self):
        acc_dashboard = self.go_to_acc_scope()
        env_page = acc_dashboard.menu.go_to_environments()
        env_page.select_active_environment(' acc1env1')
        env_page.policies_tab.click()
        env_page.link_cloud_to_environment('Configuration','selenium-policy-group-1')
        env_page.save_button.click()
        assert env_page.page_message.text == "Environment saved", \
            "No message present about successfull saving of the new Environment"
        assert env_page.linked_policy_group("selenium-policy-group-1").visible()

    @pytest.mark.skip('SCALRCORE-11738')
    def test_check_application_with_policy_tag_role(self):
        env_dashboard = self.go_to_acc_scope(switch_to_env=True)
        farms_page = env_dashboard.menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Farm1')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        category = 'Base'
        new_farm_page.add_farm_role_button.click()
        for role_name in self.roles_without_tag:
            new_farm_page.add_farm_role(category, role_name)
            new_farm_page.add_role_to_farm_button.click()
        # Blocked by SCALRCORE-11738
