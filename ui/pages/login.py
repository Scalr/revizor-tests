from pages.base import BasePage, wait_for_page_to_load
from elements.base import Button, Input, Label
from elements import locators


class LoginPage(BasePage):
    """Default Scalr login page.
    """
    loading_blocker_locator = locators.IdLocator('loading')
    login_field = Input(name='scalrLogin')
    password_field = Input(name='scalrPass')
    login_button = Button(text='Login')
    new_password_field = Input(name='password')
    confirm_password_field = Input(label='Confirm')
    update_password_button = Button(
        xpath='//span [contains(text(), "Update my password")]')

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
        from pages.environment_scope import EnvironmentDashboard
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
            if Button(class_name='x-mask', driver=self.driver).hidden():
                break
        self.update_password_button.click()
        self.password_field.write(new_password)
        self.login_button.click()
        from pages.environment_scope import EnvironmentDashboard
        return EnvironmentDashboard(self.driver, self.base_url)
