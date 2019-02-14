import time

from selenium.webdriver.support import expected_conditions as EC

from elements.base import Label, Button, Input, SearchInput, Dropdown, SplitButton, Checkbox, Menu, Combobox, TableRow
from pages.base import wait_for_page_to_load, BasePage
from pages.common import CommonTopMenu
from pages.account_scope import AccountDashboard
from pages.global_scope import AdminTopMenu


class Roles(AdminTopMenu):
    """Roles page (Admin Scope)
    """
    new_role_button = Button(text="New role")
    new_role_button_env = Button(css="[href='\#\/roles\/edit'] [unselectable]")
    roles_info = Label(
        xpath='//div [@class="x-grid-item-container"]/child::table')
    search_role_field = SearchInput(name="searchfield")
    search_role_field2 = Button(xpath="//input[@class='x-tagfield-input-field']")
    searchfield_trigger_menu = Button(css=".x-searchfield-trigger-menu-default")
    searchfield_trigger_tag_list = Button(xpath="//div[@role='presentation']/div[.='Tag']")
    roles_edit_button = Button(icon="edit")
    body_container = Button(xpath="//div[@id='body-container']")

    @property
    def loaded(self):
        return self.new_role_button.wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def new_role(self, env=False):
        """Clicks on the 'New Role' button.
           Redirects to Roles Edit page.
           Returns RolesEdit page object.
        """
        self.new_role_button.click()
        if env:
            self.new_role_button_env.click()
        return RolesEdit(self.driver, self.base_url)

    def searchfield_trigger_find_tag(self, tag_name):
        tag_from_list = "//li[contains(.,'%s')]" % tag_name
        finded_tag = Button(xpath=tag_from_list, driver=self.driver)
        assert finded_tag.visible(), "The tag was not found!"
        return finded_tag

    def roles_table_sorted_by_tag(self, tag_name):
        xpath = "//div[@class='x-tagfield-item-text x-tagfield-item-double-padding-right'][contains(.,'Tag')][contains(.,': %s')]" \
                % tag_name
        roles_table_sorted_by_tag = Button(xpath=xpath, driver=self.driver)
        return roles_table_sorted_by_tag

    def edit_role(self):
        from pages.roles import RolesEdit
        Button(icon="edit", driver=self.driver).click()
        return RolesEdit(self.driver, self.base_url)


class RolesEdit(AdminTopMenu):
    """Roles Edit page (Admin Scope).
    """
    roles_settings_label = Label(text="Bootstrap settings")
    role_name_field = Input(name="name")
    tags_dropdown = Dropdown(input_name='projectId')
    save_button = Button(xpath="//span[contains(text(),'Save')]")
    add_image_button = Button(xpath="//div[contains(text(),'Add image')]")
    add_automation_button = Button(css=".x-form-item-no-label:nth-of-type(3) .x-btn-icon-el-default-small")
    configure_automation_ok_button = Button(xpath="//span[.='OK'][@data-ref='btnInnerEl']")
    roles_table_sorted_by_roleid = Button(
        xpath="//span[@class='x-searchfield-item-label'][contains(.,'Role ID')]")
    #tags_input_field = Button(xpath="//input[@name='tags']")
    body_container = Button(xpath="//div[@id='body-container']")
    tooltip_one_policy_allowed = Button(
        xpath="//div[.='Only one Policy Tag is allowed.'][@class='x-autocontainer-innerCt']")

    @property
    def loaded(self):
        return self.roles_settings_label.wait_until_condition(EC.visibility_of_element_located)

    def add_tag_to_role(self, tag_name):
        """
        Adds a tag to the role that is being edited.
        """
        Button(xpath="//input[@name='tags']", driver=self.driver).click()
        xpath = "//li[contains(.,'%s')]" % tag_name
        Button(xpath=xpath, driver=self.driver).click()


    def os_settings(self, os_name, os_version, category, tag_name=None):
        """
        Set up OS settings in roles edit page.
        """
        li = "//li[contains(.,'%s')]"
        os_from_list = li % os_name
        Button(xpath="//input[@placeholder='Family']", driver=self.driver).click()
        Button(xpath=os_from_list, driver=self.driver).click()
        version_from_list = li % os_version
        Button(xpath="//input[@placeholder='Version']", driver=self.driver).click()
        Button(xpath=version_from_list, driver=self.driver).click()
        if tag_name:
            RolesEdit.add_tag_to_role(self, tag_name)
            RolesEdit.body_container.click()
        category_from_list = li % category
        Button(xpath="//div[starts-with(@id, 'combobox')]/input[@name='catId']", driver=self.driver).click()
        found_category = Button(xpath=category_from_list, driver=self.driver)
        found_category.wait_until_condition(EC.visibility_of_element_located)
        found_category.click()

    def add_image(self, image_name):
        """
        :param image_name:
        In roles edit page: Finds the image in the list and adds it to which role is edited.
        """
        Button(css='.x-form-empty-field .x-form-empty-field', driver=self.driver).click()
        Input(xpath="//input [starts-with(@class, 'x-tagfield-input-field')]", driver=self.driver).write(image_name)
        image = "//div[contains(text(),'%s')]" % image_name
        found_image = Button(xpath=image, driver=self.driver)
        assert found_image.visible(), "Can't find image in list"
        found_image.click()
        Button(xpath="//a[.='Add']", driver=self.driver).click()

    def created_role(self, role_name):
        """
        :param role_name:
        :return: the found role in the roles table
        """
        created_role = TableRow(text=role_name, driver=self.driver)
        return created_role

    def create_role(self, roles_edit_page, tag_name=None, automation=True, **roles_settings):
        """
        :param roles_edit_page: Page object. This is the page for creating or editing a role
         in a particular scope.
        :param roles_settings: type Dict: you can use default_role settings
        or set up settings to create roles through roles_settings variable.
        :param automation: type boolean: you can turn on/off automation
        and set configuration for automation through roles_settings = {'configure_automation': } variable
        Example configuration for automation: ['Chef', 'MySQL 5', 'PostgreSQL', 'Percona 5']
        """
        default_role = {
            'role_name': 'selenium-ubuntu1404-with-tag-admin',
            'os_name': 'Ubuntu',
            'os_version': '14.04',
            'tag_name': tag_name,
            'category': 'Base',
            'image_name': 'base-ubuntu1404-global-160825-1528',
            'configure_automation': ['Chef']
        }
        if roles_settings:
            default_role.update(roles_settings)
        if automation:
            RolesEdit.add_automation_button.click()
            for behavior in default_role['configure_automation']:
                xpath = "//span[@class='x-btn-inner x-btn-inner-simple-small'][.='%s']" % behavior
                Button(xpath=xpath, driver=self.driver).click()
            RolesEdit.configure_automation_ok_button.click()
        roles_edit_page.role_name_field.write(default_role['role_name'])
        os_name = default_role['os_name'],
        os_version = default_role['os_version'],
        category = default_role['category']
        roles_edit_page.os_settings(os_name, os_version, category, tag_name)
        roles_edit_page.add_image_button.click()
        roles_edit_page.add_image(default_role['image_name'])

        roles_edit_page.save_button.click()
        assert roles_edit_page.roles_table_sorted_by_roleid.visible(), "The roles table is not sorted by Id!"
        assert roles_edit_page.page_message.text == "Role saved", \
            "No message present about successful saving of the Role"
        assert roles_edit_page.created_role(default_role['role_name']).visible(), "Role was not found!"
        return roles_edit_page
