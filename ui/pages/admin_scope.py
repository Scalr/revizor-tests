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
    cancel_button = Button(icon="cancel")
    delete_button_before_pop_up = Button(icon="delete")
    deletion_pop_up = Button(xpath="//div[contains(.,'Delete Policy Tag ')][@class='message']")

    @property
    def loaded(self):
        return self.new_policy_tag_button.wait_until_condition(EC.visibility_of_element_located)

    def created_tag(self, tag_name=None):
        xpath = "//table[contains(.,'%s')]" % tag_name
        created_tag = Button(xpath=xpath, driver=self.driver)
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
        pop_up_button = Button(xpath=xpath, driver=self.driver).click()
