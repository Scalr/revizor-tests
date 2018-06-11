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

    def get_element(self, custom_locator=None):
        return self.list_elements()[0]

    def list_elements(self, custom_locator=None):
        locator = custom_locator or self.locator
        for _ in range(5):
            try:
                elements = [el for el in self.driver.find_elements(*locator) if el.is_displayed()]
                if elements:
                    return elements
            except StaleElementReferenceException:
                continue
            time.sleep(6)
        raise NoSuchElementException(locator[1])

    def displayed(self, timeout=3):
        start = time.time()
        while (time.time() - start) < timeout:
            elements = self.driver.find_elements(*self.locator)
            if elements and elements[0].is_displayed():
                return True
            time.sleep(3)
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
        self.get_element().click()


class Checkbox(BaseElement):

    def __init__(self, driver, value=None, xpath=None):
        super().__init__(driver)
        if value:
            self.locator = (By.XPATH, '//* [@data-value="%s"]' % value.lower())
        else:
            self.locator = (By.XPATH, xpath)

    def check(self):
        element = self.get_element()
        if 'x-cb-checked' not in element.get_attribute("class"):
            element.click()

    def uncheck(self):
        element = self.get_element()
        if 'x-cb-checked' in element.get_attribute("class"):
            element.click()


class Combobox(BaseElement):

    def __init__(self, driver, text=None, xpath=None, span=True):
        super().__init__(driver)
        self.span = span
        if text:
            self.locator = (
                By.XPATH,
                '//span[contains(text(), "%s")]//ancestor::div[starts-with(@id, "combobox")]' % text)
        else:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element().click()
        if self.span:
            option_locator = (By.XPATH, '//span[contains(text(), "%s")]//parent::li' % option)
        else:
            option_locator = (By.XPATH, '//li[contains(text(), "%s")]' % option)
        self.get_element(custom_locator=option_locator).click()


class Dropdown(BaseElement):

    def __init__(self, driver, label=None, xpath=None):
        super().__init__(driver)
        if label:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]')
        else:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element().click()
        option_locator = (By.XPATH, '//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option)
        self.get_element(custom_locator=option_locator).click()


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
        element = self.get_element()
        element.clear()
        element.send_keys(text)


class Label(BaseElement):

    def __init__(self, driver, text=None, xpath=None):
        super().__init__(driver)
        if text:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]' % text)
        else:
            self.locator = (By.XPATH, xpath)


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
        return Label(self, "Last errors").displayed()

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
        return Label(self, "Environments in this account").displayed()

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
        self.new_acl_button = Button(self, text="New ACL")
        self.name_field = Input(self, label="ACL name")
        self.permissions_filter = Input(self, label="Permissions")
        self.access_dropdown = Dropdown(self, xpath='//div [@class="x-resource-name"]//preceding-sibling::a')
        self.save_button = Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.displayed()

    def get_permission(self, name):
        return Checkbox(self, value=name)


class Users(Page):
    URL_TEMPLATE = '/#/account/users'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_user_button = Button(self, text="New user")
        self.email_field = Input(self, name="email")
        self.save_button = Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_user_button.displayed()


class Teams(Page):
    URL_TEMPLATE = '/#/account/teams'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_team_button = Button(self, text="New team")
        self.team_name_field = Input(self, name="name")
        self.acl_combobox = Combobox(self, text="Default ACL")
        self.save_button = Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_team_button.displayed()

    def add_user_to_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]' % email
        return Button(self, xpath=xpath).click()

    def remove_user_form_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return Button(self, xpath=xpath).click()


class Environments(Page):
    URL_TEMPLATE = '/#/account/environments'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_env_button = Button(self, text="New environment")
        self.env_name_field = Input(self, name="name")
        self.cost_center_combobox = Combobox(
            self,
            xpath='//span[contains(text(), "Cost center")]//ancestor::label//following-sibling::div[starts-with(@id, "combobox")]',
            span=False)
        self.access_tab = Button(self, text="Access")
        self.grant_access_menu = Button(self,text="Grant access")
        self.grant_access_button = Button(self, xpath='//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
        self.save_button = Button(self, icon="save")
        self.active_envs = Label(self, xpath='//div[starts-with(@class, "x-dataview-tab")]')

    @property
    def loaded(self):
        return self.new_env_button.displayed()

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        cloud_button = Button(self, xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % cloud_name)
        credentials = Button(self, xpath='//div [contains(text(), "%s")]//ancestor::table' % credentials_name)
        link_button = Button(self, text="Link to Environment")
        cloud_button.click()
        credentials.click()
        link_button.click()

    def grant_access(self, team):
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = Checkbox(
            self,
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        return self.active_envs.list_elements()


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
