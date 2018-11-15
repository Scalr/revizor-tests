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


class AdminTopMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_roles(self):
        """Redirects to Roles page (list of Scalr roles).
           Returns Roles page object.
        """
        Button(text="Roles", driver=self.driver).click()
        return Roles(self.driver, self.base_url)


class AdminLeftMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_policy_tags(self):
        """ Redirects to Policy Tags Page.
            Returns Admin page object.
        """
        Button(href="#/admin/policyengine/tags", driver=self.driver).click()
        return PolicyTags(self.driver, self.base_url)


class AdminDashboard(AdminLeftMenu, AdminTopMenu):
    URL_TEMPLATE = '/#/admin/dashboard'

    @property
    def loaded(self):
        return Button(
            text="Admin Dashboard", driver=self.driver).wait_until_condition(
            EC.visibility_of_element_located)


class PolicyTags(AdminLeftMenu):
    """Policy Tags page (Admin Scope).
    """
    URL_TEMPLATE = '#/admin/policyengine/tags'
    new_policy_tag_button = Button(text="New policy tag")
    name_field = Input(name="name")
    save_button = Button(icon="save")
    cancel_button = Button(icon="cancel")
    delete_button_before_pop_up = Button(icon="delete")
    deletion_pop_up = Button(xpath="//div[contains(.,'Delete Policy Tag ')][@class='message']")

    @property
    def loaded(self):
        return self.new_policy_tag_button.wait_until_condition(
            EC.visibility_of_element_located)

    def created_tag(self, name):
        created_tag = Table(text=name, driver=self.driver)
        return created_tag

    def input_alert(self, text):
        xpath = '//div[@role="alert"][.="%s"]' % text
        alert = Button(xpath=xpath, driver=self.driver)
        return alert.visible()

    def deletion_pop_up_buttons(self, action):
        """
        :param action: can be 'Cancel' or 'Delete'
        """
        xpath = "//*[.='%s']" % action
        Button(xpath=xpath, driver=self.driver).click()


class Roles(AdminTopMenu):
    """Roles page (Admin Scope)
    """
    URL_TEMPLATE = '/#/admin/roles'
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
    URL_TEMPLATE = '#/admin/roles/edit'
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
            Button(xpath=tag_from_list, driver=self.driver).click()
        category_from_list = li % category
        Button(xpath="//div[starts-with(@id, 'combobox')]/input[@name='catId']", driver=self.driver).click()
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
