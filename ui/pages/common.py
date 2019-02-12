import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pypom.exception import UsageError

from elements.base import Button, Menu
from elements.page_objects import LeftPopupMenu
from elements import locators

from pages.base import wait_for_page_to_load, BasePage
from pages.login import LoginPage


class CommonTopMenu(BasePage):
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
        return Menu(xpath='//a [contains(@class, "x-icon-avatar")]', driver=self.driver)

    @property
    def scalr_main_menu(self):
        return LeftPopupMenu(self.driver)

    @property
    def active_environment(self):
        """Returns str name of the current active Scalr environment.
        """
        for name in self.env_list:
            env = Button(text=name, driver=self.driver)
            if env.visible():
                return env
        raise NoSuchElementException("Can't find active Environment!")

    @wait_for_page_to_load
    def go_to_account(self):
        """Switches to Account level Dashboard.
           Returns AccountDashboard page object.
        """
        self.active_environment.click()
        Button(text='Main account', driver=self.driver).click()
        from pages.account_scope import AccountDashboard
        return AccountDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_admin(self):
        """Switches to Admin level Dashboard.
           Returns AdminDashboard page object.
        """
        from pages.global_scope import AdminDashboard
        return AdminDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_environment(self, env_name="acc1env1"):
        """Switches to specific Scalr environment.
           Returns EnvironmentDashboard page object.
        """
        self.active_environment.click()
        if env_name not in self.active_environment.text:
            Button(text=env_name, driver=self.driver).click()
        from pages.environment_scope import EnvironmentDashboard
        return EnvironmentDashboard(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_dashboard(self):
        """Redrects to Dashboard of current Environment/Account.
        """
        Button(text="Dashboard", driver=self.driver).click()
        return self

    def logout(self):
        """Logs out from current user session.
           Redirects to Scalr Login Page.
           Returns LoginPage object.
        """
        self.scalr_user_menu.select('Logout')
        return LoginPage(self.driver, self.base_url)
