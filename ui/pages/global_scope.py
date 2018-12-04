import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pypom import Page
from pypom.exception import UsageError

from elements import locators
from elements.base import Button, Label, Input, SearchInput, Menu, Checkbox, Combobox, Dropdown
from pages.base import wait_for_page_to_load
from pages.common import CommonTopMenu


class AdminTopMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_accounts(self):
        """Redirects to Accounts page (Global scope).
           Returns Accounts page object.
        """
        Button(href="#/admin/accounts", driver=self.driver).click()
        return Accounts(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_users(self):
        """Redirects to Users page (Global scope).
           Returns Users page object.
        """
        Button(href="#/admin/users", driver=self.driver).click()
        return Users(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_roles(self):
        """Redirect to Roles page (Global scope).
           Returns Roles page object.
        """
        Button(href="#/admin/roles", driver=self.driver).click()
        return Roles(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_images(self):
        """Redirects to Images page (Global scope).
           Returns Images page object.
        """
        Button(href="#/admin/images",
               driver=self.driver).click()
        return Images(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_scrips(self):
        """Redirects to Scripts page (Global scope).
           Returns Scripts page object.
        """
        Button(href="#/admin/scrips",
               driver=self.driver).click()
        return Scripts(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_cost_analytics(self):
        """Redirects to Analytics page (Global scope).
           Returns Analytics page object.
        """
        Button(href="#/admin/analytics/dashboard",
               driver=self.driver).click()
        return Analytics(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_webhooks(self):
        """Redirects to Webhooks Config page (Global scope).
           Returns Webhooks page object.
        """
        Button(href="#/admin/webhooks/configs",
               driver=self.driver).click()
        return WebhooksConfigs(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_endpoints(self):
        """Redirects to Webhooks Endpoint page (Global scope).
           Returns Endpoints page object.
        """
        Button(href="#/admin/webhooks/endpoints",
               driver=self.driver).click()
        return WebhooksEndpoints(self.driver, self.base_url)


class AdminDashboard(AdminTopMenu):
    URL_TEMPLATE = '/#/admin/dashboard'

    @property
    def loaded(self):
        return Button(
            href=self.URL_TEMPLATE[1:],
            driver=self.driver).wait_until_condition(EC.visibility_of_element_located)


class Accounts(AdminTopMenu):
    """Accounts page from Global Scope.
    """
    URL_TEMPLATE = '/#/admin/accounts'
    new_account_button = Button(text="New account")
    edit_account_button = Button(href="#/admin/accounts/1/edit")


    @wait_for_page_to_load
    def go_to_account(self, account_name=None):
        """Switches to Account level Dashboard.
           Returns AccountDashboard page object.
        """
        account_name = account_name or "Main account"
        Button(xpath="//div [contains(text(), '%s')]//following::a[@data-qtip='Login as owner'][1]" % account_name,
               driver=self.driver).click()
        from pages.account_scope import AccountDashboard
        return AccountDashboard(self.driver, self.base_url)

    @property
    def loaded(self):
        return self.new_account_button.wait_until_condition(EC.visibility_of_element_located)

    def open_edit_popup(self):
        self.new_account_button.click()
        return AccountEditPopup(self.driver)


class AccountEditPopup(Accounts):
    """Implements New Account popup window elements
    """
    popup_label = Label(xpath="//div [contains(text(), 'Admin » Accounts')]")
    name_field = Input(xpath="//input [@name='name']")
    owner_email_field = Button(xpath="//input [@name='ownerEmail']")
    comments_field = Input(xpath="//textarea [@name='comments']")
    cost_centers_field = Dropdown(input_name="ccs")
    create_button = Button(xpath="//span [text()='Create']//ancestor::a")
    cancel_button = Button(xpath="//span [text()='Cancel']//ancestor::a")

    @property
    def loaded(self):
        return self.popup_label.wait_until_condition(EC.visibility_of_element_located)

    def select_account_owner(self, name=None):
        actions = ActionChains(self.driver)
        name = name or 'selenium'
        self.owner_email_field.click()
        #search_btn = Button(driver=self.driver, xpath="(//div [text()='Search'])[position()=last()]")
        search_input = Input(driver=self.driver, xpath="(//div [text()='Search'])[position()=last()]//following::input")
        search_input.get_element(show_hidden=True)
        search_input.write('sdfs')
        #actions.click(search_btn)
        #actions.send_keys(search_input)
        #actions.perform()
        import time
        time.sleep(5)
        Button(driver=self.driver, xpath="//div [contains(text(), '%s')]" % name).click()
        Button(driver=self.driver, xpath="//span [text()='Select']").click()


class Users(AdminTopMenu):
    """Users page from Account scope.
    """
    URL_TEMPLATE = '/#/account/users'
    new_user_button = Button(text="New user")
    email_field = Input(name="email")
    save_button = Button(icon="save")
    admin_access_on = Button(text="On")
    admin_access_off = Button(text="Off")
    allow_to_manage_envs_checkbox = Checkbox(
        text="Allow to manage environments")

    @property
    def loaded(self):
        return self.new_user_button.wait_until_condition(EC.visibility_of_element_located)


class Roles(AdminTopMenu):
    """Roles page from Global scope.
    """
    pass


class Images(AdminTopMenu):
    """Images page from Global scope.
    """
    pass


class Scripts(AdminTopMenu):
    """Scripts page from Global scope.
    """
    pass


class Analytics(AdminTopMenu):
    """Analytics page from Global scope.
    """
    pass


class WebhooksConfigs(AdminTopMenu):
    """WebhooksConfigs page from Global scope.
    """
    pass


class WebhooksEndpoints(AdminTopMenu):
    """WebhooksEndpoints page from Global scope.
    """
    pass
