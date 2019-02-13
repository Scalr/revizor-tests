from selenium.webdriver.support import expected_conditions as EC

from elements.base import Button, Label, Input, Dropdown, TableRow, Filter
from elements.page_objects import ConfirmButton, GlobalScopeSwitchButton
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
        """Redirects to Roles page (Global scope).
           Returns Roles page object.
        """
        from pages.roles import Roles
        Button(text="Roles", driver=self.driver).click()
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


class AdminLeftMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_policy_tags(self):
        """ Redirects to Policy Tags Page.
            Returns Policy Tags page object (Global scope).
        """
        Button(href="#/admin/policyengine/tags", driver=self.driver).click()
        return PolicyTags(self.driver, self.base_url)


class AdminDashboard(AdminTopMenu, AdminLeftMenu):
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
    # page elements xpath
    _input = "//input [@name='%s']"
    _btn = "//span [text()='%s']/ancestor::a"

    # page elements
    popup_label = Label(xpath="//div [contains(text(), 'Admin » Accounts »')][contains(@class, 'x-title-text')]")
    comments_field = Input(xpath="//textarea [@name='comments']")
    cost_centers_field = Dropdown(input_name="ccs")
    name_field = Input(xpath=_input % "name")
    owner_email_field = Button(xpath=_input % "ownerEmail")
    create_button = Button(xpath=_btn % "Create")
    save_button = Button(xpath=_btn % "Save")
    cancel_button = Button(xpath=_btn % "Cancel")

    required_fields = [
        name_field,
        owner_email_field,
        cost_centers_field
    ]

    @property
    def loaded(self):
        return self.popup_label.wait_until_condition(EC.visibility_of_element_located)

    def set_account_owner(self, name):
        if self.popup_label.exists:
            self.owner_email_field.click()
        Filter(driver=self.driver).write(name)
        account_owner_table_row = TableRow(driver=self.driver, label=name)
        account_owner_table_row.wait_until_condition(EC.visibility_of_element_located)
        account_owner_table_row.select()
        Button(driver=self.driver, xpath="//span [text()='Select']").click()

    def new_account_owner_click(self):
        self.owner_email_field.click()
        Button(driver=self.driver, xpath="//span [text()='New User']").click()
        return CreateUserPanel(driver=self.driver)


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
    set_activate_button = ConfirmButton(xpath=_confirm_btn % "Activate selected users")
    set_suspended_button = ConfirmButton(xpath=_confirm_btn % "Suspend selected users")
    delete_user_button = ConfirmButton(xpath=_confirm_btn_red % "Delete selected users")
    refresh_button = Button(xpath=_confirm_btn % "Refresh")

    def new_user_click(self):
        self.new_user_button.click()
        return CreateUserPanel(driver=self.driver)

    def edit_user(self, label):
        self.user_filter.write(label)
        user_table_row = TableRow(driver=self.driver, label=label)
        user_table_row.wait_until_condition(EC.visibility_of_element_located)
        user_table_row.select()
        return EditUserPanel(driver=self.driver)

    @property
    def loaded(self):
        return self.new_user_button.wait_until_condition(EC.visibility_of_element_located)


class CreateUserPanel(Users):
    """Implements global scope new user panel
    """
    top_label_text = "New user"

    # page elements xpath
    _btn = "//span [text()='%s']/ancestor::a"
    _input_field = "//input [@name='%s']"
    _icon_btn = "//span [contains(@class, 'x-btn-icon-%s')]"

    # page elements
    full_name_field = Input(xpath=_input_field % "fullName")
    email_field = Input(xpath=_input_field % "email")
    comments_field = Input(xpath="//textarea [@name='comments']")
    password_field = Input(xpath=_input_field % "password")
    confirm_password_field = Input(xpath=_input_field % "cpassword")
    generate_password_button = GlobalScopeSwitchButton("Automatically generate a password")
    change_password_at_signin_button = GlobalScopeSwitchButton("Ask for a password change at the next sign-in")
    set_activate_button = Button(xpath=_btn % "Active")
    set_suspended_button = Button(xpath=_btn % "Suspended")
    set_global_admin_perm_button = GlobalScopeSwitchButton("Global Admin")
    set_cm_admin_perm_button = GlobalScopeSwitchButton("Cost Manager Admin")
    save_button = ConfirmButton(xpath=_icon_btn % "save")
    cancel_button = Button(xpath=_icon_btn % "cancel")

    required_fields = dict(
        user_email=email_field,
        user_password=password_field,
        user_confirm_password=confirm_password_field)

    @property
    def loaded(self):
        label = Label(xpath=f"//div [text()='{self.top_label_text}'][contains(@class, 'x-fieldset-header-text')]")
        return label.wait_until_condition(EC.visibility_of_element_located)


class EditUserPanel(CreateUserPanel):
    """Implements global scope user edit panel
    """
    top_label_text = "Edit user"
    change_user_password_button = ConfirmButton(xpath=CreateUserPanel._icon_btn % "change-password")
    delete_user_button = ConfirmButton(xpath=CreateUserPanel._icon_btn % "delete")


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


class PolicyTags(AdminLeftMenu):
    """Policy Tags page (Admin Scope).
    """
    URL_TEMPLATE = '#/admin/policyengine/tags'
    new_policy_tag_button = Button(text="New policy tag")
    name_field = Input(name="name")
    save_button = Button(icon="save")
    cancel_button = Button(icon="cancel")
    delete_button_before_pop_up = Button(icon="delete")
    deletion_pop_up = Button(xpath="//div[contains(.,'Delete Policy Tag ')][@class='message']")

    @property
    def loaded(self):
        return self.new_policy_tag_button.wait_until_condition(
            EC.visibility_of_element_located)

    def created_tag(self, name):
        created_tag = Table(text=name, driver=self.driver)
        return created_tag

    def input_alert(self, text):
        xpath = '//div[@role="alert"][.="%s"]' % text
        alert = Button(xpath=xpath, driver=self.driver)
        return alert.visible()

    def deletion_pop_up_buttons(self, action):
        """
        :param action: can be 'Cancel' or 'Delete'
        """
        xpath = "//*[.='%s']" % action
        Button(xpath=xpath, driver=self.driver).click()
