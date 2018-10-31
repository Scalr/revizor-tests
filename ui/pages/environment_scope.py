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


class EnvironmentTopMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_farms(self):
        """Redirects to Farms page (list of Scalr farms).
           Returns Farms page object.
        """
        Button(text="Farms", driver=self.driver).click()
        return Farms(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_servers(self):
        """Redirects to Servers page (list of Scalr servers).
           Returns Servers page object.
        """
        Button(text="Servers", driver=self.driver).click()
        return Servers(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_images(self):
        """ Redirects to Images Page.
            Returns Environment page object.
        """
        Button(href="#/images", driver=self.driver).click()
        return Images(self.driver, self.base_url)


class EnvironmentDashboard(EnvironmentTopMenu):
    URL_TEMPLATE = '/#/dashboard'

    @property
    def loaded(self):
        return Button(text="Dashboard", driver=self.driver).wait_until_condition(EC.visibility_of_element_located)


class Farms(EnvironmentTopMenu):
    """Farms page (Environment Scope)
    """
    URL_TEMPLATE = '/#/farms'
    new_farm_button = Button(text="New Farm")
    farms_info = Label(
        xpath='//div [@class="x-grid-item-container"]/child::table')
    search_farm_field = SearchInput(name="searchfield")

    @property
    def loaded(self):
        return self.new_farm_button.wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def new_farm(self):
        """Clicks on the 'New Farm' button.
           Redirects to Farm Designer page.
           Returns FarmDesigner page object.
        """
        self.new_farm_button.click()
        return FarmDesigner(self.driver, self.base_url)

    @wait_for_page_to_load
    def configure_farm(self, farm_id):
        """Clicks on 'Configure farm' from specified farm id.
           Redirects to Farm Designer page.
           Returns FarmDesigner page object.

           :param str farm_id: Scalr farm id.
        """
        Button(
            href='#/farms/designer?farmId=%s' % farm_id,
            driver=self.driver).click()
        return FarmDesigner(self.driver, self.base_url)

    def list_farms(self):
        """Returns list of dicts with farm info for currently available Scalr farms.
        """
        farm_elements = self.farms_info.list_elements()
        farms_info = []
        for el in farm_elements:
            info = el.text.split('\n')
            farm = {
                "farm_id": info[0],
                "name": info[1],
                "date_of_creation": info[2] + info[3] + info[4] + ',' + info[5],
                "owner": info[6],
                "state": info[-1],
                "element": el,
                "action_menu": Menu(
                    xpath='//* [@id="%s"]//child::a [@class="x-grid-action-button x-grid-action-button-showmore"]' % el.get_attribute(
                        'id'),
                    driver=self.driver)
            }
            farms_info.append(farm)
        return farms_info


class FarmDesigner(EnvironmentTopMenu):
    """Farm Designer page (Environment Scope).
    """
    URL_TEMPLATE = '#/farms/designer'
    farm_settings_label = Label(text="Farm settings")
    farm_name_field = Input(name="name")
    projects_dropdown = Dropdown(input_name='projectId')
    teams_dropdown = Dropdown(xpath='//ul [@data-ref="itemList"]')
    save_splitbutton = SplitButton()

    @property
    def loaded(self):
        return self.farm_settings_label.wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def save_farm(self, launch=False):
        """Save or Save & Launch configured farm.
           Redirects for Farms page.
           Returns Farms page object.

           :param bool launch: Launch saved farm.
        """
        if launch:
            self.save_splitbutton.click("Save & launch")
        else:
            self.save_splitbutton.click("Save farm")
        return Farms(self.driver, self.base_url)


class Images(EnvironmentTopMenu):
    URL_TEMPLATE = '/#/images'
    new_image_button = Button(text="New image")

    @property
    def loaded(self):
        return self.new_image_button.wait_until_condition(EC.visibility_of_element_located)

    def image_builder(self):
        self.new_image_button.click()
        return ImagesBuilder(self.driver, self.base_url)


class RolesBuilder(EnvironmentTopMenu):
    """Role/Image builder page.
    """
    URL_TEMPLATE = '/#/roles/builder'
    only_image_checkbox = Checkbox(
        text="Only create an Image, do not create a Role using that Image")
    name_field = Input(label="Name")
    create_button = Button(text="Create")

    @property
    def loaded(self):
        return Label(
            text="Location and operating system",
            driver=self.driver).wait_until_condition(EC.visibility_of_element_located)

    def create_role(self, os, name, behaviors=[], only_image=False):
        """Creates new role or image.
           :param os str: Name of the desired operating system as it's presented in Scalr UI.
           :param name str: Name of the new role/image.
           :param behaviors list of str: Names of the desired behaviors (software) as they are presented in Scalr UI.
           :param only_image bool: Create only image or both image and role.
        """
        Button(text=os, driver=self.driver).click()
        for behavior in behaviors:
            Button(text=behavior, driver=self.driver).click()
        self.name_field.write(name)
        if only_image:
            self.only_image_checkbox.check()
        self.create_button.click()
        label = "Image" if only_image else "Role"
        if not Label("%s creation progress" % label, driver=self.driver).wait_until_condition(EC.visibility_of_element_located):
            raise NoSuchElementException(
                "User was not redirected to %s creation page" % label)


class ImagesBuilder(RolesBuilder):
    URL_TEMPLATE = '/#/roles/builder?image'


class Servers(EnvironmentTopMenu):
    URL_TEMPLATE = '/#/servers'
    pass