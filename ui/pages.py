import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from pypom import Page


ENV_LIST = ['acc1env1', 'acc1env2', 'acc1env3', 'acc1env4', 'Selenium Env']


def return_loaded_page(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        page = func(*args, **kwargs)
        wait = WebDriverWait(page.driver, 30)
        mask_locator = (By.CLASS_NAME, "x-mask")  # Elements that obscure usage of other elements
        wait.until(
            lambda d: page.loaded,
            message="Page did not load in 30 seconds!")
        wait.until(
            lambda d: all(not mask.is_displayed() for mask in d.find_elements(*mask_locator)),
            message="Mask objects enabled for too long")
        return page
    return wrapper


class LoginPage(Page):
    _login_field_locator = (By.NAME, 'scalrLogin')
    _password_field_locator = (By.NAME, 'scalrPass')
    _login_button_locator = (By.LINK_TEXT, 'Login')
    _loading_blocker_locator = (By.ID, 'loading')

    @property
    def loaded(self):
        return not self.is_element_present(*self._loading_blocker_locator)

    @property
    def login_field(self):
        return self.find_element(*self._login_field_locator)

    @property
    def password_field(self):
        return self.find_element(*self._password_field_locator)

    @property
    def login_button(self):
        return self.find_elements(*self._login_button_locator)[1]

    @return_loaded_page
    def login(self, user, password):
        self.login_field.send_keys(user)
        self.password_field.send_keys(password)
        self.login_button.click()
        return EnvironmentDashboard(self.driver, self.base_url)


class ScalrUpperMenu(Page):
    _env_dropdown_locator = '//span [contains(text(), "{}")]//ancestor::a'
    _env_link_locator = '//span [contains(text(), "{}")]//ancestor::a [contains(@id, "menucheckitem")]'
    _account_link_locator = (By.PARTIAL_LINK_TEXT, 'Main account')

    @return_loaded_page
    def go_to_account(self):
        self.active_environment.click()
        self.find_element(*self._account_link_locator).click()
        return AccountDashboard(self.driver, self.base_url)

    @property
    def active_environment(self):
        for name in ENV_LIST:
            env = self.find_elements(*(By.XPATH, self._env_dropdown_locator.format(name)))
            if env and env[0].is_displayed():
                return env[0]

    @return_loaded_page
    def go_to_environment(self, env_name="acc1env1"):
        self.active_environment.click()
        if env_name not in self.active_environment.text:
            self.find_element(*(By.XPATH, self._env_link_locator.format(env_name))).click()
        return EnvironmentDashboard(self.driver, self.base_url)


class EnvironmentDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/dashboard'
    _errors_info_locator = (By.XPATH, '//div [contains(text(), "Last errors")]')
    _dashboard_link_locator = (By.LINK_TEXT, 'Dashboard')
    _farms_link_locator = (By.LINK_TEXT, 'Farms')
    _servers_link_locator = (By.LINK_TEXT, 'Servers')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._errors_info_locator)

    @return_loaded_page
    def go_to_dashboard(self):
        self.find_element(*self._dashboard_link_locator).click()
        return self

    @return_loaded_page
    def go_to_farms(self):
        self.find_element(*self._farms_link_locator).click()
        return Farms(self.driver, self.base_url)

    @return_loaded_page
    def go_to_servers(self):
        self.find_element(*self._servers_link_locator).click()
        return Servers(self.driver, self.base_url)


class AccountDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/account/dashboard'
    _env_info_locator = (By.XPATH, '//div [contains(text(), "Environments in this account")]')
    _dashboard_link_locator = (By.LINK_TEXT, 'Account Dashboard')
    _acl_link_locator = (By.XPATH, '//a [@href="#/account/acl"]')
    _users_link_locator = (By.XPATH, '//a [@href="#/account/users"]')
    _teams_link_locator = (By.XPATH, '//a [@href="#/account/teams"]')
    _environments_link_locator = (By.XPATH, '//a [@href="#/account/environments"]')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._env_info_locator)

    @return_loaded_page
    def go_to_acl(self):
        self.find_element(*self._acl_link_locator).click()
        return ACL(self.driver, self.base_url)

    @return_loaded_page
    def go_to_users(self):
        self.find_element(*self._users_link_locator).click()
        return Users(self.driver, self.base_url)

    @return_loaded_page
    def go_to_teams(self):
        self.find_element(*self._teams_link_locator).click()
        return Teams(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environments(self):
        self.find_element(*self._environments_link_locator).click()
        return Environments(self.driver, self.base_url)


class ACL(Page):
    URL_TEMPLATE = '/#/account/acl'
    _new_acl_locator = (By.LINK_TEXT, 'New ACL')
    _new_acl_name_field_locator = (By.XPATH, '//span [contains(text(), "ACL name")]//following::input')
    _permissions_filter_locator = (By.XPATH, '//fieldset [@class="x-fieldset x-fieldset-separator-none x-fieldset-with-title x-fieldset-with-legend x-box-item x-fieldset-default"]//child::input')
    _permissions_access_dropdown_locator = '//* [@class="x-resource-name"] [contains(text(), "{}")]/..//a' # Find "All Farms" label and get it's parent by /.. or specific parent type (//a)
    _permissions_access_options_locator = (By.XPATH, '//div [starts-with(@id, "menuitem")]')
    # _option_checkbox_base_locator = '//* [contains(text(), "{}")]//preceding::div [starts-with(@id, "ext-element")]'
    _option_checkbox_base_locator = '//* [@data-value="{}"]'
    _save_button_locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-save")]//ancestor::a')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_acl_locator)

    def new_acl(self):
        return self.find_element(*self._new_acl_locator).click()

    @property
    def new_acl_name_field(self):
        return self.find_element(*self._new_acl_name_field_locator)

    @property
    def new_acl_permissions_filter(self):
        return self.find_element(*self._permissions_filter_locator)

    def set_access(self, access_for, set_option):
        dropdown_locator = (By.XPATH, self._permissions_access_dropdown_locator.format(access_for))
        self.find_element(*dropdown_locator).click()
        for _ in range(5):
            try:
                if self.find_element(*dropdown_locator).get_attribute('id'):
                    break
            except StaleElementReferenceException:
                time.sleep(3)
                continue
        self.find_element(*dropdown_locator).click()
        for option in self.find_elements(*self._permissions_access_options_locator):
            if option.text.lower() == set_option.lower():
                return option.click()
        raise AssertionError("Option %s was not found!" % set_option)

    def click_checkbox_option(self, data_value, action='check'):
        locator = (By.XPATH, self._option_checkbox_base_locator.format(data_value.lower()))
        self.wait.until(
            lambda d: d.find_elements(*locator),
            message="Unable to find element %s in time!" % locator[1])
        checkbox = self.find_element(*locator)
        checked = 'x-cb-checked' in checkbox.get_attribute('class')
        if (not checked and action == 'check') or (checked and action == 'uncheck'):
            checkbox.click()
        return 'x-cb-checked' in self.find_element(*locator).get_attribute('class')

    def save_acl(self):
        save_buttons = self.find_elements(*self._save_button_locator)
        return [button for button in save_buttons if button.is_displayed()][0].click()


class Users(Page):
    URL_TEMPLATE = '/#/account/users'
    _new_user_link_locator = (By.XPATH, '//span [contains(text(), "New user")]//ancestor::a')
    _new_user_email_field_locator = (By.XPATH, '//input [@name="email"]')
    _save_button_locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-save")]//ancestor::a')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_user_link_locator)

    def new_user(self):
        return self.find_element(*self._new_user_link_locator).click()

    @property
    def new_user_email_field(self):
        email_fields = self.find_elements(*self._new_user_email_field_locator)
        return [field for field in email_fields if field.is_displayed()][0]

    def save_new_user(self):
        save_buttons = self.find_elements(*self._save_button_locator)
        return [button for button in save_buttons if button.is_displayed()][0].click()


class Teams(Page):
    URL_TEMPLATE = '/#/account/teams'
    _new_team_link_locator = (By.XPATH, '//span [contains(text(), "New team")]//ancestor::a')
    _new_team_name_field_locator = (By.XPATH, '//input [@name="name"]')
    _default_acl_combobox_locator = (By.XPATH, '//span[contains(text(), "Default ACL")]//ancestor::div[starts-with(@id, "combobox")]')
    _default_acl_options_locator = '//span[contains(text(), "{}")]//parent::li'
    _members_option_locator = '//*[contains(text(), "{}")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]'
    _save_button_locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-save")]//ancestor::a')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_team_link_locator)

    def new_team(self):
        return self.find_element(*self._new_team_link_locator).click()

    @property
    def new_team_name_field(self):
        name_fields = self.find_elements(*self._new_team_name_field_locator)
        return [field for field in name_fields if field.is_displayed()][0]

    def select_default_acl(self, acl_name):
        self.find_element(*self._default_acl_combobox_locator).click()
        option_locator = (By.XPATH, self._default_acl_options_locator.format(acl_name))
        return self.find_element(*option_locator).click()

    def add_user_to_team(self, email):
        member_locator = (By.XPATH, self._members_option_locator.format(email))
        return self.find_element(*member_locator).click()

    def save_team(self):
        save_buttons = self.find_elements(*self._save_button_locator)
        return [button for button in save_buttons if button.is_displayed()][0].click()


class Environments(Page):
    URL_TEMPLATE = '/#/account/environments'
    _new_env_link_locator = (By.XPATH, '//span [contains(text(), "New environment")]//ancestor::a')
    _new_env_name_field_locator = (By.XPATH, '//input [@name="name"]')
    _cost_center_combobox_locator = (By.XPATH, '//span[contains(text(), "Cost center")]//ancestor::div[starts-with(@id, "combobox")]')
    _cost_center_options_locator = '//li[contains(text(), "{}")]'
    _cloud_options_locator = '//div [contains(text(), "{}")]//ancestor::table//child::a'
    _cloud_credentials_options_locator = '//div [contains(text(), "{}")]//ancestor::table'
    _link_button_locator = (By.XPATH, '//span [contains(text(), "Link to Environment")]//ancestor::a')
    _access_tab_link_locator = (By.XPATH, '//span [contains(text(), "Access")]//ancestor::a')
    _grant_access_menu_button_locator = (By.XPATH, '//span [contains(text(), "Grant access")]//ancestor::a[contains(@class, "x-btn-green")]')
    _grant_access_team_checkbox_locator = '//div [contains(text(), "Users")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]'
    _grant_access_to_teams_button_locator = (By.XPATH, '//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
    _save_button_locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-save")]//ancestor::a')
    _active_envs_locator = (By.XPATH, '//div[starts-with(@class, "x-dataview-tab")]')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_env_link_locator)

    def new_environment(self):
        return self.find_element(*self._new_env_link_locator).click()

    @property
    def new_environment_name_field(self):
        name_fields = self.find_elements(*self._new_env_name_field_locator)
        return [field for field in name_fields if field.is_displayed()][0]

    def select_cost_center(self, name):
        self.find_element(*self._cost_center_combobox_locator).click()
        option_locator = (By.XPATH, self._cost_center_options_locator.format(name))
        return self.find_element(*option_locator).click()

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        cloud_locator = (By.XPATH, self._cloud_options_locator.format(cloud_name))
        credentials_locator = (By.XPATH, self._cloud_credentials_options_locator.format(credentials_name))
        self.find_element(*cloud_locator).click()
        self.wait.until(
            lambda d: self.is_element_displayed(*credentials_locator),
            message="Can't find cloud credentials!")
        self.find_element(*credentials_locator).click()
        return self.find_element(*self._link_button_locator).click()

    def grant_access(self, team):
        self.find_element(*self._access_tab_link_locator).click()
        self.find_element(*self._grant_access_menu_button_locator).click()
        team_checkbox_locator = (By.XPATH, self._grant_access_team_checkbox_locator.format(team))
        self.find_element(*team_checkbox_locator).click()
        self.find_element(*self._grant_access_to_teams_button_locator).click()

    def list_environments(self):
        envs = [env.text for env in self.find_elements(*self._active_envs_locator) if env.is_displayed()]
        return envs

    def save_environment(self):
        return self.find_element(*self._save_button_locator).click()


class Farms(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'
    _new_farm_link_locator = (By.LINK_TEXT, "New Farm")
    _farms_item_locator = (By.XPATH, '//div [@class="x-grid-item-container"]/child::table')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_farm_link_locator)

    @return_loaded_page
    def new_farm(self):
        self.find_element(*self._new_farm_link_locator).click()
        return FarmDesigner(self.driver, self.base_url)

    def list_farms(self):
        farm_elements = [el for el in self.find_elements(*self._farms_item_locator) if el.is_displayed()]
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


    def search_farms(self, search_condition):
        [el for el in self.find_elements(*(By.TAG_NAME, 'div')) if 'searchfield' in el.get_attribute('id')][0].click() # Activate input
        input_field = [el for el in self.find_elements(*(By.TAG_NAME, 'input')) if 'searchfield' in el.get_attribute('id')][0]
        input_field.clear()
        return input_field.send_keys(search_condition)


class FarmDesigner(ScalrUpperMenu):
    URL_TEMPLATE = '#/farms/designer'
    _farm_settings_label_locator = (By.XPATH, '//div [contains(text(), "Farm settings")]')
    _farm_name_field_locator = (By.XPATH, '//input [@name="name"]')
    _projects_dropdown_locator = (By.XPATH, '//span [contains(text(), "Project")]//ancestor::div [contains(@id, "costanalyticsproject")]')
    _project_option_locator = '//span [contains(text(), "{}")]//parent::div//parent::div[starts-with(@class, "x-boundlist-item")]'
    _teams_dropdown_locator = (By.XPATH, '//span [contains(text(), "Team")]//ancestor::div [starts-with(@id, "teamfield")]')
    _team_option_locator = '//b [contains(text(), "{}")]//parent::div'
    _save_launch_farm_splitbutton_locator = (By.XPATH, '//span [contains(text(), "Save & launch")]//ancestor::a [starts-with(@id, "splitbutton")]')
    _save_farm_splitbutton_locator = (By.XPATH, '//span [contains(text(), "Save farm")]//ancestor::a [starts-with(@id, "splitbutton")]')
    _save_launch_farm_option_locator = (By.XPATH, '//span [contains(text(), "Save & launch")]//ancestor::a [starts-with(@id, "menuitem")]')
    _save_farm_option_locator = (By.XPATH, '//span [contains(text(), "Save farm")]//ancestor::a [starts-with(@id, "menuitem")]')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._farm_settings_label_locator)

    @property
    def farm_name_field(self):
        name_fields = self.find_elements(*self._farm_name_field_locator)
        return [field for field in name_fields if field.is_displayed()][0]

    def select_project(self, project_name):
        dropdown = [e for e in self.find_elements(*self._projects_dropdown_locator)
            if e.is_displayed()][0]
        dropdown.click()
        option_locator = (By.XPATH, self._project_option_locator.format(project_name))
        self.find_element(*option_locator).click()

    def select_teams(self, team_names):
        dropdown = [e for e in self.find_elements(*self._teams_dropdown_locator)
            if e.is_displayed()][0]
        dropdown.click()
        for name in team_names:
            option_locator = (By.XPATH, self._team_option_locator.format(name))
            self.find_element(*option_locator).click()

    @return_loaded_page
    def save_farm(self, launch=False):
        if self.is_element_displayed(*self._save_farm_splitbutton_locator) and not launch:
            self.find_element(*self._save_farm_splitbutton_locator).click()
        elif self.is_element_displayed(*self._save_launch_farm_splitbutton_locator) and launch:
            self.find_element(*self._save_launch_farm_splitbutton_locator).click()
        else:
            current_button_locator = self._save_farm_splitbutton_locator if launch else self._save_launch_farm_splitbutton_locator
            current_button = self.find_element(*current_button_locator)
            chain = ActionChains(self.driver)
            chain.move_to_element(current_button)
            chain.move_by_offset(50, 0)
            chain.click()
            chain.perform()
            locator = self._save_launch_farm_option_locator if launch else self._save_farm_option_locator
            self.find_element(*locator).click()
        return Farms(self.driver, self.base_url)


class Servers(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'
    pass
