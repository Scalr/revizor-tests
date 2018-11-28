import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from pypom import Page
from pypom.exception import UsageError

from elements import locators
from elements.base import Button, Label, Input, SearchInput, Menu, Checkbox, Combobox
from pages.base import wait_for_page_to_load
from pages.common import CommonTopMenu


class AccountTopMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_acl(self):
        """Redirects to ACL page (Account scope).
           Returns ACL page object.
        """
        Button(href="#/account/acl", driver=self.driver).click()
        return ACL(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_users(self):
        """Redirects to Users page (Account scope).
           Returns Users page object.
        """
        Button(href="#/account/users", driver=self.driver).click()
        return Users(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_teams(self):
        """Redirect to Teams page (Account scope).
           Returns Teams page object.
        """
        Button(href="#/account/teams", driver=self.driver).click()
        return Teams(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_environments(self):
        """Redirects to Environments page (Account scope).
           Returns Environments page object.
        """
        Button(href="#/account/environments",
               driver=self.driver).click()
        return Environments(self.driver, self.base_url)


class AccountLeftMenu(CommonTopMenu):

    def go_to_roles(self):
        """Redirects to Roles page (list of Scalr roles).
           Returns Roles page object.
        """
        from pages.roles import Roles
        Button(xpath="//a[@role='menuitem']/span[.='Roles Library']", driver=self.driver).click()
        return Roles(self.driver, self.base_url)


class AccountDashboard(AccountTopMenu, AccountLeftMenu):
    URL_TEMPLATE = '/#/account/dashboard'

    @property
    def loaded(self):
        return Label(
            "Environments in this account",
            driver=self.driver).wait_until_condition(EC.visibility_of_element_located)


class ACL(AccountTopMenu):
    """ACL page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/acl'
    new_acl_button = Button(text="New ACL")
    name_field = Input(label="ACL name")
    permissions_filter = SearchInput(label="Permissions")
    save_button = Button(icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.wait_until_condition(EC.visibility_of_element_located)

    def set_access(self, access_for, access_type):
        """Set specified access level for specified Scalr property.

           :param str access_for: name of the Scalr property.
           :param str access_type: desired access level (Full Access/Limited/Read Only/ No Access).
        """
        menu = Menu(label=access_for, driver=self.driver)
        menu.select(access_type)

    def get_permission(self, name, label=None):
        """Returns Checkbox object for specific permission.

           :param str name: Name(text) of the permission.
        """
        if label:
            return Checkbox(
                xpath='//* [contains(text(), "%s")]//parent::* [@data-value="%s"]' % (
                    label, name.lower()),
                driver=self.driver)
        else:
            return Checkbox(value=name, driver=self.driver)


class Users(AccountTopMenu):
    """Users page from Account scope.
    """
    URL_TEMPLATE = '/#/account/users'
    new_user_button = Button(text="New user")
    email_field = Input(name="email")
    save_button = Button(icon="save")
    admin_access_on = Button(text="On")
    admin_access_off = Button(text="Off")
    allow_to_manage_envs_checkbox = Checkbox(
        text="Allow to manage environments")

    @property
    def loaded(self):
        return self.new_user_button.wait_until_condition(EC.visibility_of_element_located)


class Teams(AccountTopMenu):
    """Teams page from Account scope.
    """
    URL_TEMPLATE = '/#/account/teams'
    new_team_button = Button(text="New team")
    team_name_field = Input(name="name")
    acl_combobox = Combobox(text="Default ACL")
    save_button = Button(icon="save")

    @property
    def loaded(self):
        return self.new_team_button.wait_until_condition(EC.visibility_of_element_located)

    def add_user_to_team(self, email):
        """Adds specified User to currently selected Team.

           :param str email: user email.
        """
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]' % email
        return Button(xpath=xpath, driver=self.driver).click()

    def remove_user_from_team(self, email):
        """Removes specified User from currently selected Team.

           :param str email: user email.
        """
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return Button(xpath=xpath, driver=self.driver).click()


class Environments(AccountTopMenu):
    """Environments page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/environments'
    new_env_button = Button(text="New environment")
    env_name_field = Input(name="name")
    cost_center_combobox = Combobox(
        xpath='//span[contains(text(), "Cost center")]//ancestor::label//following-sibling::div[starts-with(@id, "combobox")]',
        span=False)
    access_tab = Button(text="Access")
    grant_access_menu = Button(text="Grant access")
    grant_access_button = Button(
        xpath='//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
    save_button = Button(icon="save")
    active_envs = Label(
        xpath='//div[starts-with(@class, "x-dataview-tab")]')

    @property
    def loaded(self):
        return self.new_env_button.wait_until_condition(EC.visibility_of_element_located)

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        """Links cloud (by cloud name) to currently selected Scalr Environment
           with specified Scalr credentials.

           :param str cloud_name: Cloud name (abbreviation) as it's displayed in Scalr UI.
           :param str credentials_name: name of the cloud credentials.
        """
        cloud_button = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % cloud_name,
            driver=self.driver)
        credentials = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table' % credentials_name,
            driver=self.driver)
        link_button = Button(
            text="Link to Environment", driver=self.driver)
        cloud_button.click()
        credentials.click()
        link_button.click()

    def grant_access(self, team):
        """Grant access to currently selected Scalr Environment to specified Scalr team.

           :param str team: Scalr team name.
        """
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = Checkbox(
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team,
            driver=self.driver)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        """Returns list of Elements of available Scalr Environments.
        """
        return self.active_envs.list_elements()
