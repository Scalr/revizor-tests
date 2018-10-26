import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from pypom import Page
from pypom.exception import UsageError

from elements.base import Label, Button, Input, SearchInput, Dropdown, SplitButton, Checkbox, Menu
from elements import locators
from pages.base import wait_for_page_to_load, BasePage
from pages.common import CommonTopMenu


class AdminLeftMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_policy_tags(self):
        """ Redirects to Policy Tags Page.
            Returns Admin page object.
        """
        Button(href="#/admin/policyengine/tags", driver=self.driver).click()
        return PolicyTags(self.driver, self.base_url)


class AdminDashboard(AdminLeftMenu):
    URL_TEMPLATE = '/#/admin/dashboard'

    @property
    def loaded(self):
        return Button(text="Admin Dashboard", driver=self.driver).wait_until_condition(EC.visibility_of_element_located)


class PolicyTags(AdminLeftMenu):
    """Policy Tags page (Admin Scope).
    """
    URL_TEMPLATE = '#/admin/policyengine/tags'
    new_policy_tag_button = Button(text="New policy tag")
    name_field = Input(name="name")
    save_button = Button(icon="save")

    # farm_settings_label = Label(text="Farm settings")
    # farm_name_field = Input(name="name")
    # projects_dropdown = Dropdown(input_name='projectId')
    # teams_dropdown = Dropdown(xpath='//ul [@data-ref="itemList"]')
    # save_splitbutton = SplitButton()
    # new_image_button = Button(text="New image")

    @property
    def loaded(self):
        return self.new_policy_tag_button.wait_until_condition(EC.visibility_of_element_located)


