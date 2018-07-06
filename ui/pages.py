import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pypom import Page

import elements
import locators


def return_loaded_page(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        page = func(*args, **kwargs)
        mask = locators.ClassLocator("x-mask")
        for _ in range(10):
            if page.loaded and all(not el.is_displayed() for el in page.driver.find_elements(*mask)):
                return page
            time.sleep(3)
        raise Exception("Page did not load in 30 seconds.")
    return wrapper


class BasePage(Page):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for el in self.__class__.__dict__.values():
            if isinstance(el, elements.BaseElement):
                el.driver = self.driver


class LoginPage(BasePage):
    loading_blocker_locator = (By.ID, 'loading')
    login_field = elements.Input(name='scalrLogin')
    password_field = elements.Input(name='scalrPass')
    login_button = elements.Button(text='Login')

    @property
    def loaded(self):
        return not self.is_element_present(*self.loading_blocker_locator)

    @return_loaded_page
    def login(self, user, password):
        self.login_field.write(user)
        self.password_field.write(password)
        self.login_button.click()
        return EnvironmentDashboard(self.driver, self.base_url)


class ScalrUpperMenu(BasePage):
    env_list = ['acc1env1', 'acc1env2', 'acc1env3', 'acc1env4', 'Selenium Env']

    @property
    def active_environment(self):
        for name in self.env_list:
            env = elements.Button(text=name, driver=self.driver)
            if env.visible():
                return env
        raise NoSuchElementException("Can't find active Environment!")

    @return_loaded_page
    def go_to_account(self):
        self.active_environment.click()
        elements.Button(text='Main account', driver=self.driver).click()
        return AccountDashboard(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environment(self, env_name="acc1env1"):
        self.active_environment.click()
        if env_name not in self.active_environment.text:
            elements.Button(text=env_name, driver=self.driver).click()
        return EnvironmentDashboard(self.driver, self.base_url)


class EnvironmentDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/dashboard'

    @property
    def loaded(self):
        return elements.Label("Last errors", driver=self.driver).visible()

    @return_loaded_page
    def go_to_dashboard(self):
        elements.Button(text="Dashboard", driver=self.driver).click()
        return self

    @return_loaded_page
    def go_to_farms(self):
        elements.Button(text="Farms", driver=self.driver).click()
        return Farms(self.driver, self.base_url)

    @return_loaded_page
    def go_to_servers(self):
        elements.Button(text="Servers", driver=self.driver).click()
        return Servers(self.driver, self.base_url)


class AccountDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/account/dashboard'

    @property
    def loaded(self):
        return elements.Label("Environments in this account", driver=self.driver).visible()

    @return_loaded_page
    def go_to_acl(self):
        elements.Button(href="#/account/acl", driver=self.driver).click()
        return ACL(self.driver, self.base_url)

    @return_loaded_page
    def go_to_users(self):
        elements.Button(href="#/account/users", driver=self.driver).click()
        return Users(self.driver, self.base_url)

    @return_loaded_page
    def go_to_teams(self):
        elements.Button(href="#/account/teams", driver=self.driver).click()
        return Teams(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environments(self):
        elements.Button(href="#/account/environments", driver=self.driver).click()
        return Environments(self.driver, self.base_url)


class ACL(BasePage):
    URL_TEMPLATE = '/#/account/acl'
    new_acl_button = elements.Button(text="New ACL")
    name_field = elements.Input(label="ACL name")
    permissions_filter = elements.Input(label="Permissions")
    save_button = elements.Button(icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.visible()

    def set_access(self, access_for, access_type):
        menu = elements.Menu(label=access_for, driver=self.driver)
        menu.select(access_type)

    def get_permission(self, name):
        return elements.Checkbox(value=name, driver=self.driver)


class Users(BasePage):
    URL_TEMPLATE = '/#/account/users'
    new_user_button = elements.Button(text="New user")
    email_field = elements.Input(name="email")
    save_button = elements.Button(icon="save")

    @property
    def loaded(self):
        return self.new_user_button.visible()


class Teams(BasePage):
    URL_TEMPLATE = '/#/account/teams'
    new_team_button = elements.Button(text="New team")
    team_name_field = elements.Input(name="name")
    acl_combobox = elements.Combobox(text="Default ACL")
    save_button = elements.Button(icon="save")

    @property
    def loaded(self):
        return self.new_team_button.visible()

    def add_user_to_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]' % email
        return elements.Button(xpath=xpath, driver=self.driver).click()

    def remove_user_form_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return elements.Button(xpath=xpath, driver=self.driver).click()


class Environments(BasePage):
    URL_TEMPLATE = '/#/account/environments'
    new_env_button = elements.Button(text="New environment")
    env_name_field = elements.Input(name="name")
    cost_center_combobox = elements.Combobox(
        xpath='//span[contains(text(), "Cost center")]//ancestor::label//following-sibling::div[starts-with(@id, "combobox")]',
        span=False)
    access_tab = elements.Button(text="Access")
    grant_access_menu = elements.Button(text="Grant access")
    grant_access_button = elements.Button(xpath='//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
    save_button = elements.Button(icon="save")
    active_envs = elements.Label(xpath='//div[starts-with(@class, "x-dataview-tab")]')

    @property
    def loaded(self):
        return self.new_env_button.visible()

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        cloud_button = elements.Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % cloud_name,
            driver=self.driver)
        credentials = elements.Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table' % credentials_name,
            driver=self.driver)
        link_button = elements.Button(text="Link to Environment", driver=self.driver)
        cloud_button.click()
        credentials.click()
        link_button.click()

    def grant_access(self, team):
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = elements.Checkbox(
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team,
            driver=self.driver)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        return self.active_envs.list_elements()


class Farms(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'
    new_farm_button = elements.Button(text="New Farm")
    farms_info = elements.Label(xpath='//div [@class="x-grid-item-container"]/child::table')
    search_farm_field = elements.Input(name="searchfield")

    @property
    def loaded(self):
        return self.new_farm_button.visible()

    @return_loaded_page
    def new_farm(self):
        self.new_farm_button.click()
        return FarmDesigner(self.driver, self.base_url)

    def list_farms(self):
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
                "element": el
            }
            farms_info.append(farm)
        return farms_info


class FarmDesigner(ScalrUpperMenu):
    URL_TEMPLATE = '#/farms/designer'
    farm_settings_label = elements.Label(text="Farm settings")
    farm_name_field = elements.Input(name="name")
    projects_dropdown = elements.Dropdown(input_name='projectId')
    teams_dropdown = elements.Dropdown(xpath='//ul [@data-ref="itemList"]')
    save_splitbutton = elements.SplitButton()

    @property
    def loaded(self):
        return self.farm_settings_label.visible()

    @return_loaded_page
    def save_farm(self, launch=False):
        if launch:
            self.save_splitbutton.click("Save & launch")
        else:
            self.save_splitbutton.click("Save farm")
        return Farms(self.driver, self.base_url)


class Servers(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'
    pass
