import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pypom import Page
from pypom.exception import UsageError

import elements
import locators


def wait_for_page_to_load(func, *args, **kwargs):
    """Waits until all 'mask' elements will become hidden and Page loaded == True,
       then returns the page object.
    """
    def wrapper(*args, **kwargs):
        page = func(*args, **kwargs)
        mask = locators.ClassLocator("x-mask")
        for _ in range(10):
            if page.loaded and all(not el.is_displayed() for el in page.driver.find_elements(*mask)):
                return page
            time.sleep(3)
        raise UsageError("Page did not load in 30 seconds.")
    return wrapper


class BasePage(Page):
    """Base class for custom PyPOM Page.
       Sets selenium driver property
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for el in self.__class__.__dict__.values():
            if isinstance(el, elements.BaseElement):
                el.driver = self.driver


class LoginPage(BasePage):
    """Default Scalr login page.
    """
    loading_blocker_locator = (By.ID, 'loading')
    login_field = elements.Input(name='scalrLogin')
    password_field = elements.Input(name='scalrPass')
    login_button = elements.Button(text='Login')
    new_password_field = elements.Input(name='password')
    confirm_password_field = elements.Input(label='Confirm')
    update_password_button = elements.Button(xpath='//span [contains(text(), "Update my password")]')

    @property
    def loaded(self):
        return not self.is_element_present(*self.loading_blocker_locator)

    @wait_for_page_to_load
    def login(self, user, password):
        """Logs in with existing user.
           Returns EnvironmentDashboard page obejct.

           :param str user: username(email).
           :param str password: user password
        """
        self.login_field.write(user)
        self.password_field.write(password)
        self.login_button.click()
        return EnvironmentDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def update_password_and_login(self, user, temp_password, new_password):
        """Logs in as the new user with temporary password.
           Sets new password and returns EnvironmentsDashboard page object.

           :param str user: username (email).
           :param str temp_password: temporary password.
           :param str new_password: new password.
        """
        self.login_field.write(user)
        self.password_field.write(temp_password)
        self.login_button.click()
        self.new_password_field.write(new_password)
        self.confirm_password_field.write(new_password)
        for _ in range(5):
            if elements.Button(class_name='x-mask', driver=self.driver).hidden():
                break
        self.update_password_button.click()
        self.password_field.write(new_password)
        self.login_button.click()
        return EnvironmentDashboard(self.driver, self.base_url)


class Menu(BasePage):
    """Combines Scalr top menu and main (dropdown) menu.
       Used as a Base class from some Scalr page Classes.
    """
    env_list = ['acc1env1', 'acc1env2', 'acc1env3', 'acc1env4', 'Selenium Env']

    @property
    def menu(self):
        return self

    @property
    def scalr_user_menu(self):
        """Scalr User menu (click on user's avatar).
        """
        return elements.Menu(xpath='//a [contains(@class, "x-icon-avatar")]', driver=self.driver)

    @property
    def scalr_main_menu(self):
        return elements.ScalrMainMenu(self.driver)

    @property
    def active_environment(self):
        """Returns str name of the current active Scalr environment.
        """
        for name in self.env_list:
            env = elements.Button(text=name, driver=self.driver)
            if env.visible():
                return env
        raise NoSuchElementException("Can't find active Environment!")

    @wait_for_page_to_load
    def go_to_account(self):
        """Switches to Account level Dashboard.
           Returns AccountDashboard page object.
        """
        self.active_environment.click()
        elements.Button(text='Main account', driver=self.driver).click()
        return AccountDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_environment(self, env_name="acc1env1"):
        """Switches to specific Scalr environment.
           Returns EnvironmentDashboard page object.
        """
        self.active_environment.click()
        if env_name not in self.active_environment.text:
            elements.Button(text=env_name, driver=self.driver).click()
        return EnvironmentDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_dashboard(self):
        """Redrects to Dashboard of current Environment/Account.
        """
        elements.Button(text="Dashboard", driver=self.driver).click()
        return self

    @wait_for_page_to_load
    def go_to_farms(self):
        """Redirects to Farms page (list of Scalr farms).
           Returns Farms page object.
        """
        elements.Button(text="Farms", driver=self.driver).click()
        return Farms(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_servers(self):
        """Redirects to Servers page (list of Scalr servers).
           Returns Servers page object.
        """
        elements.Button(text="Servers", driver=self.driver).click()
        return Servers(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_acl(self):
        """Redirects to ACL page (Account scope).
           Returns ACL page object.
        """
        elements.Button(href="#/account/acl", driver=self.driver).click()
        return ACL(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_users(self):
        """Redirects to Users page (Account scope).
           Returns Users page object.
        """
        elements.Button(href="#/account/users", driver=self.driver).click()
        return Users(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_teams(self):
        """Redirect to Teams page (Account scope).
           Returns Teams page object.
        """
        elements.Button(href="#/account/teams", driver=self.driver).click()
        return Teams(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_environments(self):
        """Redirects to Environments page (Account scope).
           Returns Environments page object.
        """
        elements.Button(href="#/account/environments", driver=self.driver).click()
        return Environments(self.driver, self.base_url)

    def logout(self):
        """Logs out from current user session.
           Redirects to Scalr Login Page.
           Returns LoginPage object.
        """
        self.scalr_user_menu.select('Logout')
        return LoginPage(self.driver, self.base_url)


class EnvironmentDashboard(Menu):
    URL_TEMPLATE = '/#/dashboard'

    @property
    def loaded(self):
        return elements.Button(text="Dashboard", driver=self.driver).visible()


class AccountDashboard(Menu):
    URL_TEMPLATE = '/#/account/dashboard'

    @property
    def loaded(self):
        return elements.Label("Environments in this account", driver=self.driver).visible()


class ACL(Menu):
    """ACL page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/acl'
    new_acl_button = elements.Button(text="New ACL")
    name_field = elements.Input(label="ACL name")
    permissions_filter = elements.Input(label="Permissions")
    save_button = elements.Button(icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.visible()

    def set_access(self, access_for, access_type):
        """Set specified access level for specified Scalr property.

           :param str access_for: name of the Scalr property.
           :param str access_type: desired access level (Full Access/Limited/Read Only/ No Access).
        """
        menu = elements.Menu(label=access_for, driver=self.driver)
        menu.select(access_type)

    def get_permission(self, name, label=None):
        """Returns Checkbox object for specific permission.

           :param str name: Name(text) of the permission.
        """
        if label:
            return elements.Checkbox(
                xpath='//* [contains(text(), "%s")]//parent::* [@data-value="%s"]' % (label, name.lower()),
                driver=self.driver)
        else:
            return elements.Checkbox(value=name, driver=self.driver)


class Users(Menu):
    """Users page from Account scope.
    """
    URL_TEMPLATE = '/#/account/users'
    new_user_button = elements.Button(text="New user")
    email_field = elements.Input(name="email")
    save_button = elements.Button(icon="save")
    admin_access_on = elements.Button(text="On")
    admin_access_off = elements.Button(text="Off")
    allow_to_manage_envs_checkbox = elements.Checkbox(
        text="Allow to manage environments")

    @property
    def loaded(self):
        return self.new_user_button.visible()


class Teams(Menu):
    """Teams page from Account scope.
    """
    URL_TEMPLATE = '/#/account/teams'
    new_team_button = elements.Button(text="New team")
    team_name_field = elements.Input(name="name")
    acl_combobox = elements.Combobox(text="Default ACL")
    save_button = elements.Button(icon="save")

    @property
    def loaded(self):
        return self.new_team_button.visible()

    def add_user_to_team(self, email):
        """Adds specified User to currently selected Team.

           :param str email: user email.
        """
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]' % email
        return elements.Button(xpath=xpath, driver=self.driver).click()

    def remove_user_from_team(self, email):
        """Removes specified User from currently selected Team.

           :param str email: user email.
        """
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return elements.Button(xpath=xpath, driver=self.driver).click()


class Environments(Menu):
    """Environments page from Account Scope.
    """
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
        """Links cloud (by cloud name) to currently selected Scalr Environment
           with specified Scalr credentials.

           :param str cloud_name: Cloud name (abbreviation) as it's displayed in Scalr UI.
           :param str credentials_name: name of the cloud credentials.
        """
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
        """Grant access to currently selected Scalr Environment to specified Scalr team.

           :param str team: Scalr team name.
        """
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = elements.Checkbox(
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team,
            driver=self.driver)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        """Returns list of Elements of available Scalr Environments.
        """
        return self.active_envs.list_elements()


class Farms(Menu):
    """Farms page (Environment Scope)
    """
    URL_TEMPLATE = '/#/farms'
    new_farm_button = elements.Button(text="New Farm")
    farms_info = elements.Label(xpath='//div [@class="x-grid-item-container"]/child::table')
    search_farm_field = elements.Input(name="searchfield")

    @property
    def loaded(self):
        return self.new_farm_button.visible()

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
        elements.Button(href='#/farms/designer?farmId=%s' % farm_id, driver=self.driver).click()
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
                "action_menu": elements.Menu(
                    xpath='//* [@id="%s"]//child::a [@class="x-grid-action-button x-grid-action-button-showmore"]' % el.get_attribute('id'),
                    driver=self.driver)
            }
            farms_info.append(farm)
        return farms_info


class FarmDesigner(Menu):
    """Farm Designer page (Environment Scope).
    """
    URL_TEMPLATE = '#/farms/designer'
    farm_settings_label = elements.Label(text="Farm settings")
    farm_name_field = elements.Input(name="name")
    projects_dropdown = elements.Dropdown(input_name='projectId')
    teams_dropdown = elements.Dropdown(xpath='//ul [@data-ref="itemList"]')
    save_splitbutton = elements.SplitButton()

    @property
    def loaded(self):
        return self.farm_settings_label.visible()

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


class Servers(Menu):
    URL_TEMPLATE = '/#/farms'
    pass
