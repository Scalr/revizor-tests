import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pypom import Page

import elements


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loading_blocker_locator = (By.ID, 'loading')
        self.login_field = elements.Input(self, name='scalrLogin')
        self.password_field = elements.Input(self, name='scalrPass')
        self.login_button = elements.Button(self, text='Login')

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
        self.account_link = elements.Button(self, text='Main account')

    @property
    def active_environment(self):
        for name in self.env_list:
            env = elements.Button(self, text=name)
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
            elements.Button(self, text=env_name).click()
        return EnvironmentDashboard(self.driver, self.base_url)


class EnvironmentDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/dashboard'

    @property
    def loaded(self):
        return elements.Label(self, "Last errors").displayed()

    @return_loaded_page
    def go_to_dashboard(self):
        elements.Button(self, text="Dashboard").click()
        return self

    @return_loaded_page
    def go_to_farms(self):
        elements.Button(self, text="Farms").click()
        return Farms(self.driver, self.base_url)

    @return_loaded_page
    def go_to_servers(self):
        elements.Button(self, text="Servers").click()
        return Servers(self.driver, self.base_url)


class AccountDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/account/dashboard'

    @property
    def loaded(self):
        return elements.Label(self, "Environments in this account").displayed()

    @return_loaded_page
    def go_to_acl(self):
        elements.Button(self, href="#/account/acl").click()
        return ACL(self.driver, self.base_url)

    @return_loaded_page
    def go_to_users(self):
        elements.Button(self, href="#/account/users").click()
        return Users(self.driver, self.base_url)

    @return_loaded_page
    def go_to_teams(self):
        elements.Button(self, href="#/account/teams").click()
        return Teams(self.driver, self.base_url)

    @return_loaded_page
    def go_to_environments(self):
        elements.Button(self, href="#/account/environments").click()
        return Environments(self.driver, self.base_url)


class ACL(Page):
    URL_TEMPLATE = '/#/account/acl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_acl_button = elements.Button(self, text="New ACL")
        self.name_field = elements.Input(self, label="ACL name")
        self.permissions_filter = elements.Input(self, label="Permissions")
        self.save_button = elements.Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.displayed()

    def set_access(self, access_for, access_type):
        menu = elements.Menu(self, label=access_for)
        menu.select(access_type)

    def get_permission(self, name):
        return elements.Checkbox(self, value=name)


class Users(Page):
    URL_TEMPLATE = '/#/account/users'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_user_button = elements.Button(self, text="New user")
        self.email_field = elements.Input(self, name="email")
        self.save_button = elements.Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_user_button.displayed()


class Teams(Page):
    URL_TEMPLATE = '/#/account/teams'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_team_button = elements.Button(self, text="New team")
        self.team_name_field = elements.Input(self, name="name")
        self.acl_combobox = elements.Combobox(self, text="Default ACL")
        self.save_button = elements.Button(self, icon="save")

    @property
    def loaded(self):
        return self.new_team_button.displayed()

    def add_user_to_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Add to team"]' % email
        return elements.Button(self, xpath=xpath).click()

    def remove_user_form_team(self, email):
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return elements.Button(self, xpath=xpath).click()


class Environments(Page):
    URL_TEMPLATE = '/#/account/environments'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_env_button = elements.Button(self, text="New environment")
        self.env_name_field = elements.Input(self, name="name")
        self.cost_center_combobox = elements.Combobox(
            self,
            xpath='//span[contains(text(), "Cost center")]//ancestor::label//following-sibling::div[starts-with(@id, "combobox")]',
            span=False)
        self.access_tab = elements.Button(self, text="Access")
        self.grant_access_menu = elements.Button(self,text="Grant access")
        self.grant_access_button = elements.Button(self, xpath='//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
        self.save_button = elements.Button(self, icon="save")
        self.active_envs = elements.Label(self, xpath='//div[starts-with(@class, "x-dataview-tab")]')

    @property
    def loaded(self):
        return self.new_env_button.displayed()

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        cloud_button = elements.Button(self, xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % cloud_name)
        credentials = elements.Button(self, xpath='//div [contains(text(), "%s")]//ancestor::table' % credentials_name)
        link_button = elements.Button(self, text="Link to Environment")
        cloud_button.click()
        credentials.click()
        link_button.click()

    def grant_access(self, team):
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = elements.Checkbox(
            self,
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        return self.active_envs.list_elements()


class Farms(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_farm_button = elements.Button(self, text="New Farm")
        self.farms_info = elements.Label(self, xpath='//div [@class="x-grid-item-container"]/child::table')
        self.search_farm_field = elements.Input(self, name="searchfield")

    @property
    def loaded(self):
        return self.new_farm_button.displayed()

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.farm_settings_label = elements.Label(self, text="Farm settings")
        self.farm_name_field = elements.Input(self, name="name")
        self.projects_dropdown = elements.Dropdown(self, input_name='projectId')
        self.teams_dropdown = elements.Dropdown(self, xpath='//ul [@data-ref="itemList"]')
        self.save_splitbutton = elements.SplitButton(self)

    @property
    def loaded(self):
        return self.farm_settings_label.displayed()

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
