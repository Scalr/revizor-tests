import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from pypom import Page
from pypom.exception import UsageError

from elements.base import Label, Button, Input, SearchInput, Dropdown, SplitButton, Checkbox, Menu, Combobox, Table
from elements import locators
from pages.base import wait_for_page_to_load, BasePage
from pages.common import CommonTopMenu
from pages.account_scope import AccountDashboard
from pages.admin_scope import AdminTopMenu


class Roles(AdminTopMenu):
    """Roles page (Admin Scope)
    """
    # URL_TEMPLATE = '/#/admin/roles'
    new_role_button = Button(text="New role")
    roles_info = Label(
        xpath='//div [@class="x-grid-item-container"]/child::table')
    search_role_field = SearchInput(name="searchfield")

    @property
    def loaded(self):
        return self.new_role_button.wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def new_role(self):
        """Clicks on the 'New Role' button.
           Redirects to Roles Edit page.
           Returns RolesEdit page object.
        """
        self.new_role_button.click()
        return RolesEdit(self.driver, self.base_url)


class RolesEdit(AdminTopMenu):
    """Roles Edit page (Admin Scope).
    """
    # URL_TEMPLATE = '#/admin/roles/edit'
    roles_settings_label = Label(text="Bootstrap settings")
    role_name_field = Input(name="name")
    tags_dropdown = Dropdown(input_name='projectId')
    save_button = Button(xpath="//span[contains(text(),'Save')]")
    add_image_button = Button(xpath="//div[contains(text(),'Add image')]")
    roles_table_sorted_by_roleid = Button(
        xpath="//span[@class='x-searchfield-item-label'][contains(.,'Role ID')]")

    @property
    def loaded(self):
        return self.roles_settings_label.wait_until_condition(EC.visibility_of_element_located)

    def os_settings(self, os_name, os_version, category, tag_name=None):
        li = "//li[contains(.,'%s')]"
        os_from_list = li % os_name
        Button(xpath="//input[@placeholder='Family']", driver=self.driver).click()
        Button(xpath=os_from_list, driver=self.driver).click()
        version_from_list = li % os_version
        Button(xpath="//input[@placeholder='Version']", driver=self.driver).click()
        Button(xpath=version_from_list, driver=self.driver).click()
        if tag_name:
            tag_from_list = li % tag_name
            Button(xpath="//input[@name='tags']", driver=self.driver).click()
            time.sleep(1)
            Button(xpath=tag_from_list, driver=self.driver).click()
            time.sleep(1)
        category_from_list = li % category
        Button(xpath="//div[starts-with(@id, 'combobox')]/input[@name='catId']", driver=self.driver).click()
        time.sleep(1)
        found_category = Button(xpath=category_from_list, driver=self.driver)
        found_category.wait_until_condition(EC.visibility_of_element_located)
        found_category.click()

    def add_image(self, image_name):
        Button(css='.x-form-empty-field .x-form-empty-field', driver=self.driver).click()
        Input(xpath="//input [starts-with(@class, 'x-tagfield-input-field')]", driver=self.driver).write(image_name)
        image = "//div[contains(text(),'%s')]" % image_name
        found_image = Button(xpath=image, driver=self.driver)
        assert found_image.visible(), "Can't find image in list"
        found_image.click()
        Button(xpath="//a[.='Add']", driver=self.driver).click()

    def created_role(self, role_name):
        created_role = Table(text=role_name, driver=self.driver)
        return created_role

    def create_role(self, roles_edit_page, tag_name=None, **roles_settings):
        role = {
            'role_name': 'selenium-role-policy-tag',
            'os_name': 'Ubuntu',
            'os_version': '14.04',
            'tag_name': tag_name,
            'category': 'Base',
            'image_name': 'base-ubuntu1404-global-160825-1528'
        }
        if roles_settings:
            role.update(roles_settings)
        roles_edit_page.role_name_field.write(role['role_name'])
        os_name = role['os_name'],
        os_version = role['os_version'],
        category = role['category']
        roles_edit_page.os_settings(os_name, os_version, category, tag_name)
        roles_edit_page.add_image_button.click()
        roles_edit_page.add_image(role['image_name'])
        roles_edit_page.save_button.click()
        assert roles_edit_page.roles_table_sorted_by_roleid.visible(), "The roles table is not sorted by Id!"
        assert roles_edit_page.page_message.text == "Role saved", \
            "No message present about successful saving of the Role"
        assert roles_edit_page.created_role(role['role_name']).visible(), "Role was not found!"
        return roles_edit_page
