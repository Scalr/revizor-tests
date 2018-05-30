import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from pypom import Page


def return_loaded_page(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        page = func(*args, **kwargs)
        wait = WebDriverWait(page.driver, 30)
        wait.until(
            lambda d: page.loaded,
            message="Page did not load in 30 seconds!")
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
    _environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small"]')
    _inactive_enrivonments_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-unchecked"]')
    _active_environment_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-checked x-menu-item-active"]')
    _account_link_locator = (By.PARTIAL_LINK_TEXT, 'Main account')
    _mask_locator = (By.CLASS_NAME, "x-mask")  # Elements that obscure usage of other elements

    @property
    def environments(self):
        if self.is_element_displayed(*self._environments_link_locator):
            self.find_element(*self._environments_link_locator).click()
            self._environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small x-focus x-btn-focus x-btn-default-toolbar-small-focus"]')
        environments = self.find_elements(*self._inactive_enrivonments_locator)
        environments.append(self.find_element(*self._active_environment_locator))
        return environments

    @return_loaded_page
    def go_to_account(self):
        self.wait.until(
            lambda d: all(not mask.is_displayed() for mask in d.find_elements(*self._mask_locator)),
            message="Mask objects enabled for too long")

        if self.is_element_displayed(*self._environments_link_locator):
            self.find_element(*self._environments_link_locator).click()
            self._environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small x-focus x-btn-focus x-btn-default-toolbar-small-focus"]')
        self.find_element(*self._account_link_locator).click()
        return AccountDashboard(self.driver, self.base_url)


class EnvironmentDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/dashboard'
    _errors_info_locator = (By.XPATH, '//div [contains(text(), "Last errors")]')
    _dashboard_link_locator = (By.LINK_TEXT, 'Dashboard')
    # _environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small"]')
    # _inactive_enrivonments_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-unchecked"]')
    # _active_environment_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-checked x-menu-item-active"]')
    # _account_link_locator = (By.PARTIAL_LINK_TEXT, 'Main account')
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

    @property
    def loaded(self):
        return self.is_element_displayed(*self._env_info_locator)

    @return_loaded_page
    def go_to_acl(self):
        acl = [e for e in self.find_elements(*self._acl_link_locator) if e.is_displayed()]
        if acl:
            acl[0].click()
        else:
            raise Exception(self.find_elements(*self._acl_link_locator))
        return ACL(self.driver, self.base_url)


class ACL(Page):
    URL_TEMPLATE = '/#/account/acl'
    _new_acl_locator = (By.LINK_TEXT, 'New ACL')
    _new_acl_name_field_locator = (By.XPATH, '//span [contains(text(), "ACL name")]//following::input')
    _permissions_filter_locator = (By.XPATH, '//fieldset [@class="x-fieldset x-fieldset-separator-none x-fieldset-with-title x-fieldset-with-legend x-box-item x-fieldset-default"]//child::input')
    _permissions_access_dropdown_locator = '//* [@class="x-resource-name"] [contains(text(), "{}")]/..//a' # Find "All Farms" label and get it's parent by /.. or specific parent type (//a)
    _permissions_access_options_locator = (By.XPATH, '//div [starts-with(@id, "menuitem")]')
    # _option_checkbox_base_locator = '//* [contains(text(), "{}")]//preceding::div [starts-with(@id, "ext-element")]'
    _option_checkbox_base_locator = '//* [@data-value="{}"]'
    _save_button_locator = (By.XPATH, "//a [@class='x-btn x-unselectable x-box-item x-btn-default-small undefined x-btn-button-icon x-focus x-btn-focus x-btn-default-small-focus']")

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
        for _ in range(3):
            try:
                if self.find_element(*dropdown_locator).get_attribute('id'):
                    break
            except StaleElementReferenceException:
                time.sleep(3)
                continue
        self.find_element(*dropdown_locator).click()
        for option in self.driver.find_elements(*self._permissions_access_options_locator):
            if option.text.lower() == set_option.lower():
                return option.click()
        raise AssertionError("Option %s was not found!" % set_option)

    def click_checkbox_option(self, data_value, action='check'):
        locator = (By.XPATH, self._option_checkbox_base_locator.format(data_value.lower()))
        checkbox = self.find_element(*locator)
        checked = 'x-cb-checked' in checkbox.get_attribute('class')
        if (not checked and action == 'check') or (checked and action == 'uncheck'):
            checkbox.click()
        return 'x-cb-checked' in self.find_element(*locator).get_attribute('class')

    def click_save(self):
        return self.find_element(*self._save_button_locator).click()


class Farms(ScalrUpperMenu):
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


class Servers(ScalrUpperMenu):
    URL_TEMPLATE = '/#/farms'
