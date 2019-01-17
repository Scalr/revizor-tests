import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pypom import Page
from pypom.exception import UsageError

from elements import locators
from elements.base import Button, Label, Input, SearchInput, Menu, Checkbox, Combobox, Dropdown, TableRow, Filter
from elements.page_objects import ConfirmButton
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
    delete_account_button = ConfirmButton(xpath="//a [@data-qtip='Delete'][contains(@class, 'x-btn-red')]")

    @wait_for_page_to_load
    def go_to_account(self, account_name=None):
        """Switches to Account level Dashboard.
           Returns AccountDashboard page object.
        """
        account_name = account_name or "Main account"
        TableRow(label=account_name).click_button(hint="Login as owner'")
        from pages.account_scope import AccountDashboard
        return AccountDashboard(self.driver, self.base_url)

    @property
    def loaded(self):
        return self.new_account_button.wait_until_condition(EC.visibility_of_element_located)

    def new_account_click(self):
        self.new_account_button.click()
        return AccountEditPopup(self.driver)

    def edit_account_click(self, label):
        table_row = TableRow(driver=self.driver, label=label)
        table_row.click_button(hint='Edit')
        return AccountEditPopup(self.driver)


class AccountEditPopup(Accounts):
    """Implements New Account popup window elements
    """
    _input = "//input [@name='%s']"
    _btn = "//span [text()='%s']/ancestor::a"

    popup_label = Label(xpath="//div [contains(text(), 'Admin » Accounts')]")
    name_field = Input(xpath=_input % "name")
    owner_email_field = Button(xpath=_input % "ownerEmail")
    comments_field = Input(xpath="//textarea [@name='comments']")
    cost_centers_field = Dropdown(input_name="ccs")
    create_button = Button(xpath=_btn % "Create")
    save_button = Button(xpath=_btn % "Save")
    cancel_button = Button(xpath=_btn % "Cancel")

    @property
    def loaded(self):
        return self.popup_label.wait_until_condition(EC.visibility_of_element_located)

    def select_account_owner(self, name, use_filter=False):
        self.owner_email_field.click()
        if use_filter:
            Filter().write(name)
        TableRow(driver=self.driver, label=name).select()
        Button(driver=self.driver, xpath="//span [text()='Select']").click()


class Users(AdminTopMenu):
    """Users page from Global scope.
    """
    URL_TEMPLATE = '/#/admin/users'
    # page elements xpath
    _confirm_btn = "//a [@data-qtip='%s'][contains(@class, 'x-btn')]"
    _confirm_btn_red = "//a [@data-qtip='%s'][contains(@class, 'x-btn-red')]"
    # page elements
    new_user_button = Button(text="New User")
    user_filter = Filter()
    activate_user_button = ConfirmButton(xpath=_confirm_btn % "Activate selected users")
    suspend_user_button = ConfirmButton(xpath=_confirm_btn % "Suspend selected users")
    delete_user_button = ConfirmButton(xpath=_confirm_btn_red % "Delete selected users")

    @property
    def loaded(self):
        return self.new_user_button.wait_until_condition(EC.visibility_of_element_located)


class UserCreatePanel(Users):
    """Implements global scope new user panel
    """
    top_label_text = "New user"

    # page elements xpath
    _btn = "//span [text()='%s']/ancestor::a"
    _switch_btn = "//label [text()='%s']/preceding-sibling::input [@type='button'][@role='checkbox']"
    _input_field = "//input [@name='%s']"
    _icon_btn = "//span [contains(@class, 'x-btn-icon-%s')]"

    # page elements
    full_name_field = Input(xpath=_input_field % "fullName")
    email_field = Input(xpath=_input_field % "email")
    comments_field = Input(xpath="//textarea [@name='comments']")
    password_field = Input(xpath=_input_field % "password")
    confirm_password_field = Input(xpath=_input_field % "cpassword")
    generate_password_button = Button(xpath=_switch_btn % "Automatically generate a password")
    change_password_at_signin_button = Button(xpath=_switch_btn % "Ask for a password change at the next sign-in")
    activate_user_button = Button(xpath=_btn % "Active")
    suspend_user_button = Button(xpath=_btn % "Suspended")
    set_global_admin_perm_button = Button(xpath=_switch_btn % "Global Admin")
    set_cm_admin_perm_button = Button(xpath=_switch_btn % "Cost Manager Admin")
    save_button = Button(xpath=_icon_btn % "save")
    cancel_button = Button(xpath=_icon_btn % "cancel")

    @property
    def loaded(self):
        label = Label(xpath=f"//div [text()='{self.top_label_text}'][contains(@class, 'x-fieldset-header-text')]")
        return label.wait_until_condition(EC.visibility_of_element_located)


class UserEditPanel(UserCreatePanel):
    """Implements global scope user edit panel
    """
    top_label_text = "Edit user"
    change_user_password_button = Button(xpath=UserCreatePanel._icon_btn % "change-password")
    delete_user_button = ConfirmButton(xpath=UserCreatePanel._icon_btn % "delete")


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
