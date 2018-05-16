import pytest
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from pypom import Page


class LoginPage(Page):
    _login_field_locator = (By.NAME, 'scalrLogin')
    _password_field_locator = (By.NAME, 'scalrPass')
    _login_button_locator = (By.ID, 'button-1031')
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
        return self.find_element(*self._login_button_locator)

    def login(self, user, password):
        self.login_field.send_keys(user)
        self.password_field.send_keys(password)
        self.login_button.click()
        return True


class Dashboard(Page):
    URL_TEMPLATE = '/#/dashboard'
    _dashboard_link_locator = (By.LINK_TEXT, 'Dashboard')
    _farms_link_locator = (By.LINK_TEXT, 'Farms')
    _servers_link_locator = (By.LINK_TEXT, 'Servers')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._dashboard_link_locator)

    def go_to_dashboard(self):
        self.find_element(*self._dashboard_link_locator).click()
        return self

    def go_to_farms(self):
        self.find_element(*self._farms_link_locator).click()
        return Farms(self.driver, self.base_url)

    def go_to_servers(self):
        self.find_element(*self._servers_link_locator).click()
        return Servers(self.driver, self.base_url)


class Farms(Dashboard):
    URL_TEMPLATE = '/#/farms'
    _new_farm_link_locator = (By.LINK_TEXT, "New Farm")

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_farm_link_locator)

    def search_farms(self, search_condition):
        [el for el in self.find_elements(*(By.TAG_NAME, 'div')) if 'searchfield' in el.get_attribute('id')][0].click() # Activate input
        input_field = [el for el in self.find_elements(*(By.TAG_NAME, 'input')) if 'searchfield' in el.get_attribute('id')][0]
        input_field.clear()
        return input_field.send_keys(search_condition)


class Servers(Dashboard):
    URL_TEMPLATE = '/#/farms'


class TestScalr():
    @pytest.fixture(autouse=True)
    def firefox_options(self, firefox_options):
        firefox_options.add_argument('-headless')
        return firefox_options

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium):
        # capabilities = webdriver.DesiredCapabilities().FIREFOX
        # capabilities['moz:firefoxOptions'] = {'args': ['-headless']}
        # self.driver = webdriver.Remote(
        #     command_executor='http://localhost:4444/wd/hub',
        #     desired_capabilities=capabilities)
        self.driver = selenium

    def test_login_page(self):
        # login_page = LoginPage(webdriver.Firefox(), 'http://e52f57837402.test-env.scalr.com').open()
        login_page = LoginPage(self.driver, 'http://e52f57837402.test-env.scalr.com').open()
        login_page.login('test@scalr.com', '^Qb?${q8DB')
        dashboard_page = Dashboard(login_page.driver, login_page.base_url)
        login_page.wait.until(
            lambda d: d.current_url == dashboard_page.seed_url,
            message='Wrong URL %s' % login_page.driver.current_url)
        assert dashboard_page.loaded, "Dashboard did not load"
        # login_page.driver.close()

    # def test_login_page2(self):
    #     page = LoginPage(self.driver, 'http://e52f57837402.test-env.scalr.com').open()
    #     page.login_field().send_keys('test@scalr.com')
    #     page.password_field().send_keys('^Qb?${q8DB')
    #     page.login_button().click()
    #     page.wait.until(
    #         lambda s: page.driver.current_url == 'http://e52f57837402.test-env.scalr.com/#/dashboard',
    #         message='Wrong URL %s' % page.driver.current_url)
    #     assert page.is_element_displayed(*(By.LINK_TEXT, 'Dashboard')), "Can't locate 'Dashboard' button!"
    #     page.driver.close()

    # def test_login_page3(self):
    #     page = LoginPage(self.driver, 'http://e52f57837402.test-env.scalr.com').open()
    #     page.login_field().send_keys('test@scalr.com')
    #     page.password_field().send_keys('^Qb?${q8DB')
    #     page.login_button().click()
    #     page.wait.until(
    #         lambda s: page.driver.current_url == 'http://e52f57837402.test-env.scalr.com/#/dashboard',
    #         message='Wrong URL %s' % page.driver.current_url)
    #     assert page.is_element_displayed(*(By.LINK_TEXT, 'FOO')), "Can't locate 'Dashboard' button!"
    #     page.driver.close()

