from elements.base import Button, Menu
from elements.page_objects import LeftPopupMenu

from pages.base import wait_for_page_to_load, BasePage
from pages.login import LoginPage


class CommonTopMenu(BasePage):
    """Combines Scalr top menu and main (dropdown) menu.
       Used as a Base class from some Scalr page Classes.
    """

    @property
    def menu(self):
        return self

    @property
    def scope_user_menu(self):
        """User menu (click on user's avatar).
        """
        return Menu(xpath='//a [contains(@class, "x-icon-avatar")]', driver=self.driver)

    @property
    def scope_main_menu(self):
        return LeftPopupMenu(self.driver)

    @property
    def login_as(self):
        self.scope_user_menu.click()
        return self.driver.find_element_by_xpath("//div[@class='x-username']").text

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
        self.scope_user_menu.select('Logout')
        return LoginPage(self.driver, self.base_url)
