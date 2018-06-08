import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from pypom import Page


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


class BaseElement():

    def __init__(self, driver):
        self.driver = driver
        self.locator = None

    def get_element(self, locator):
        for i in range(5):
            try:
                elements = [el for el in self.driver.find_elements(*locator) if el.is_displayed()]
                if elements:
                    return elements[0]
            except StaleElementReferenceException:
                time.sleep(3)
        raise NoSuchElementException(locator[1])

    @property
    def displayed(self):
        elements = self.driver.find_elements(*self.locator)
        if elements and elements[0].is_displayed():
            return True
        return False


class Button(BaseElement):

    def __init__(self, driver, name=None, text=None, href=None, icon=None, xpath=None):
        super().__init__(driver)
        if name:
            self.locator = (By.NAME, name)
        elif text:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]//ancestor::a' % text)
        elif href:
            self.locator = (By.XPATH, '//a [@href="%s"]' % href)
        elif icon:
            self.locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        else:
            self.locator = (By.XPATH, xpath)

    def click(self):
        self.get_element(self.locator).click()


class Checkbox(BaseElement):

    def __init__(self, driver, value=None, xpath=None):
        super().__init__(driver)
        if value:
            self.locator = (By.XPATH, '//* [@data-value="%s"]' % value.lower())
        else:
            self.locator = (By.XPATH, xpath)

    def check(self):
        element = self.get_element(self.locator)
        if 'x-cb-checked' not in element.get_attribute("class"):
            element.click()

    def uncheck(self):
        element = self.get_element(self.locator)
        if 'x-cb-checked' in element.get_attribute("class"):
            element.click()


class Dropdown(BaseElement):

    def __init__(self, driver, label=None, xpath=None):
        super().__init__(driver)
        if label:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]')
        else:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element(self.locator).click()
        option_locator = (By.XPATH, '//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option)
        self.get_element(option_locator).click()


class Input(BaseElement):

    def __init__(self, driver, name=None, label=None, xpath=None):
        super().__init__(driver)
        if name:
            self.locator = (By.NAME, name)
        elif label:
            self.locator = (By.XPATH, '//* [contains(text(),"%s")]//following::input' % label)
        else:
            self.locator = (By.XPATH, xpath)

    def write(self, text):
        element = self.get_element(self.locator)
        element.clear()
        element.send_keys(text)


class Label(BaseElement):

    def __init__(self, driver, text):
        super().__init__(driver)
        self.locator = (By.XPATH, '//* [contains(text(), "%s")]' % text)


class LoginPage(Page):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loading_blocker_locator = (By.ID, 'loading')
        self.login_field = Input(self, name='scalrLogin')
        self.password_field = Input(self, name='scalrPass')
        self.login_button = Button(self, text='Login')

    @property
    def loaded(self):
        return not self.is_element_present(*self.loading_blocker_locator)

    @return_loaded_page
    def login(self, user, password):
        self.login_field.write(user)
        self.password_field.write(password)
        self.login_button.click()
        return EnvironmentDashboard(self.driver, self.base_url)


class ScalrUpperMenu(Page):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env_list = ['acc1env1', 'acc1env2', 'acc1env3', 'acc1env4', 'Selenium Env']
        self.account_link = Button(self, text='Main account')

    @property
    def active_environment(self):
        for name in self.env_list:
            env = Button(self, text=name)
            if env.displayed:
                return env
        raise NoSuchElementException("Can't find active Environment!")

    @return_loaded_page
    def go_to_account(self):
        self.active_environment.click()
        self.account_link.click()
        return AccountDashboard(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environment(self, env_name="acc1env1"):
        self.active_environment.click()
        if env_name not in self.active_environment.text:
            Button(self, text=env_name).click()
        return EnvironmentDashboard(self.driver, self.base_url)


class EnvironmentDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/dashboard'

    @property
    def loaded(self):
        return Label(self, "Last errors").displayed

    @return_loaded_page
    def go_to_dashboard(self):
        Button(self, text="Dashboard").click()
        return self

    @return_loaded_page
    def go_to_farms(self):
        Button(self, text="Farms").click()
        return Farms(self.driver, self.base_url)

    @return_loaded_page
    def go_to_servers(self):
        Button(self, text="Servers").click()
        return Servers(self.driver, self.base_url)


class AccountDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/account/dashboard'

    @property
    def loaded(self):
        return Label(self, "Environments in this account").displayed

    @return_loaded_page
    def go_to_acl(self):
        Button(self, href="#/account/acl").click()
        return ACL(self.driver, self.base_url)

    @return_loaded_page
    def go_to_users(self):
        Button(self, href="#/account/users").click()
        return Users(self.driver, self.base_url)

    @return_loaded_page
    def go_to_teams(self):
        Button(self, href="#/account/teams").click()
        return Teams(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environments(self):
        Button(self, href="#/account/environments").click()
        return Environments(self.driver, self.base_url)


class ACL(Page):
    URL_TEMPLATE = '/#/account/acl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_acl = Button(self, text="New ACL")
        self.name_field = Input(self, label="ACL name")
        self.permissions_filter = Input(self, label="Permissions")
        self.access_dropdown = Dropdown(self, xpath='//div [@class="x-resource-name"]//preceding-sibling::a')
        self.save_button = Button(self, icon="save")

    @property
    def loaded(self):
        return Button(self, text="New ACL").displayed

    def get_permission(self, name):
        return Checkbox(self, value=name)


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
