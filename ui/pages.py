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


class ScalrUpperMenu(Page):
    _environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small"]')
    _inactive_enrivonments_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-unchecked"]')
    _active_environment_locator = (By.XPATH, '//div [@class="x-menu-item x-menu-item-default x-box-item x-menu-item-checked x-menu-item-active"]')
    _account_link_locator = (By.PARTIAL_LINK_TEXT, 'Main account')

    @property
    def environments(self):
        if self.is_element_displayed(*self._environments_link_locator):
            self.find_element(*self._environments_link_locator).click()
            self._environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small x-focus x-btn-focus x-btn-default-toolbar-small-focus"]')
        environments = self.find_elements(*self._inactive_enrivonments_locator)
        environments.append(self.find_element(*self._active_environment_locator))
        return environments

    def go_to_account(self):
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

    # @property
    # def environments(self):
    #     if self.is_element_displayed(*self._environments_link_locator):
    #         self.find_element(*self._environments_link_locator).click()
    #         self._environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small x-focus x-btn-focus x-btn-default-toolbar-small-focus"]')
    #     environments = self.find_elements(*self._inactive_enrivonments_locator)
    #     environments.append(self.find_element(*self._active_environment_locator))
    #     return environments

    # def go_to_account(self):
    #     if self.is_element_displayed(*self._environments_link_locator):
    #         self.find_element(*self._environments_link_locator).click()
    #         self._environments_link_locator = (By.XPATH, '//a [@class="x-btn x-btn-environment x-unselectable x-box-item x-toolbar-item x-btn-default-toolbar-small x-focus x-btn-focus x-btn-default-toolbar-small-focus"]')
    #     self.find_element(*self._account_link_locator).click()
    #     return AccountDashboard(self.driver, self.base_url)

    def go_to_dashboard(self):
        self.find_element(*self._dashboard_link_locator).click()
        return self

    def go_to_farms(self):
        self.find_element(*self._farms_link_locator).click()
        return Farms(self.driver, self.base_url)

    def go_to_servers(self):
        self.find_element(*self._servers_link_locator).click()
        return Servers(self.driver, self.base_url)


class AccountDashboard(ScalrUpperMenu):
    URL_TEMPLATE = '/#/account/dashboard'
    _env_info_locator = (By.XPATH, '//div [contains(text(), "Environments in this account")]')
    _dashboard_link_locator = (By.LINK_TEXT, 'Account Dashboard')
    _acl_link_locator = (By.LINK_TEXT, 'ACL')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._env_info_locator)

    def go_to_acl(self):
        self.find_element(*self._acl_link_locator).click()
        return ACL(self.driver, self.base_url)


class ACL(Page):
    URL_TEMPLATE = '/#/account/acl'
    _new_acl_locator = (By.LINK_TEXT, 'New ACL')
    _new_acl_name_field_locator = (By.XPATH, '//input [@class="x-form-field x-form-required-field x-form-text x-form-text-default  x-form-focus x-field-form-focus x-field-default-form-focus"]')
    _permissions_filter_locator = (By.XPATH, '//input [@class="x-form-field x-form-text x-form-text-default  x-form-focus x-field-form-focus x-field-default-form-focus"]')
    _permissions_all_farms_access_dropdown = (By.XPATH, '//div [contains(text(), "All Farms")]/..//a') # Find "All Farms" label and get it's parent by /.. or specific parent type (//a)
    _permissions_access_options_locator = (By.XPATH, '//div [@role="menuitem"]')

    @property
    def loaded(self):
        return self.is_element_displayed(*self._new_acl_locator)

    def new_acl(self):
        return self.find_element(*self._new_acl_locator).click()

    def new_acl_name_field(self):
        return self.find_element(*self._new_acl_name_field_locator)

    def new_acl_permissions_filter(self):
        return self.find_element(*self._permissions_filter_locator)

    def all_farms_access_options(self):
        self.find_element(*self._permissions_all_farms_access_dropdown).click()
        return self.find_elements(*self._permissions_access_options_locator)

    def get_all_checkbox_options(self, clause_object):
        





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