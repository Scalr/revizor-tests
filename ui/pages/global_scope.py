import typing as tp

from selenium.webdriver.support import expected_conditions as EC

from elements.base import Button, Label, Input, Dropdown, TableRow, Filter, Checkbox, Image, FileInput, \
    CollapsibleFieldset, Table
from elements.page_objects import ConfirmButton, GlobalScopeSwitchButton, CostManagerTagsGrid
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

    @wait_for_page_to_load
    def go_to_cloud_credentials(self) -> 'CloudCredentials':
        """Redirects to Cloud Credentials page (Global scope).
           Returns CloudCredentials page object.
        """
        self.scope_main_menu.click()
        self.scope_main_menu.select("Cloud Credentials")
        return CloudCredentials(self.driver, self.base_url)


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
        account_name = account_name or 'Main account'
        xpath = "//tr[contains(.,'%s')]/td/div/a[@data-qtip='Login as owner']" % account_name
        Button(xpath=xpath, driver=self.driver).click()
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


class PolicyTags(AdminLeftMenu):
    """Policy Tags page (Admin Scope).
    """
    URL_TEMPLATE = '#/admin/policyengine/tags'
    new_policy_button = Button(text="New policy tag")
    name_field = Input(name="name")
    save_button = Button(icon="save")
    cancel_button = Button(icon="cancel")
    delete_button_before_pop_up = Button(icon="delete")
    deletion_pop_up = Button(xpath="//div[contains(.,'Delete Policy Tag ')][@class='message']")
    deletion_message = Button(
            xpath="//div[.='Policy Tag successfully deleted'][@class='x-component x-box-item x-component-default']")

    @property
    def loaded(self):
        return self.new_policy_button.wait_until_condition(
            EC.visibility_of_element_located)

    def new_policy_tag_button(self):
        new_policy_button = Button(text="New policy tag", driver=self.driver)
        new_policy_button.wait_until_condition(EC.staleness_of, timeout=1)
        return new_policy_button

    def created_tag(self, name):
        created_tag = TableRow(text=name, driver=self.driver)
        created_tag.wait_until_condition(EC.visibility_of_element_located)
        return created_tag

    def alert_visible(self, text):
        xpath = '//div[@role="alert"][.="%s"]' % text
        alert = Button(xpath=xpath, driver=self.driver)
        alert.wait_until_condition(EC.staleness_of, timeout=1)
        return alert.visible()

    def deletion_pop_up_buttons(self, action):
        """
        :param action: can be 'Cancel' or 'Delete'
        """
        xpath = "//*[.='%s']" % action
        Button(xpath=xpath, driver=self.driver).click()


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


class CloudCredentials(AdminTopMenu):
    """Cloud Credentials page from Global scope
    """
    URL_TEMPLATE = '/#/admin/credentials'
    TITLE = 'Cloud Credentials'

    add_ccs_button = Button(xpath="//div[contains(@class, 'x-docked-top')]"
                                  "//*[text()='Add Credentials']/ancestor::a")
    refresh_button = Button(xpath="//*[text()='Add Credentials']/ancestor::div[contains(@class, 'x-docked-top')]"
                                  "//span[contains(@class, 'x-btn-icon-refresh')]")
    delete_button = ConfirmButton(xpath="//*[text()='Add Credentials']/ancestor::div[contains(@class, 'x-docked-top')]"
                                        "//span[contains(@class, 'x-btn-icon-delete')]")
    ccs_table = Table(xpath="//div[contains(@class, 'x-abs-layout-item') and not(contains(@style,'display: none'))]"
                            "//div[contains(@class, 'x-grid-view')]")
    check_all_checkbox = Button(xpath="//div[contains(@class, 'x-column-header-checkbox')]")

    def add(self, cloud: str):
        self.add_ccs_button.click()
        EditCcPanelBase(driver=self.driver).cloud_field.select(cloud)
        return CC_EDITOR[cloud](driver=self.driver)

    @wait_for_page_to_load
    def refresh(self):
        self.refresh_button.click()
        return self

    @wait_for_page_to_load
    def select(self, name: str):
        row = TableRow(driver=self.driver, label=name)
        row.select()
        return CC_EDITOR[row.data['Cloud']](driver=self.driver)

    def check(self, name: tp.Union[str, tp.List[str]]):
        if isinstance(name, str):
            name = [name]
        for n in name:
            row = TableRow(driver=self.driver, label=n)
            row.check()
        return self

    def check_all(self):
        if 'x-grid-hd-checker-on' not in self.check_all_checkbox.classes:
            self.check_all_checkbox.click()
        return self

    def uncheck_all(self):
        if 'x-grid-hd-checker-on' in self.check_all_checkbox.classes:
            self.check_all_checkbox.click()
        return self

    def list(self):
        return [row.data for row in self.ccs_table.rows]

    @wait_for_page_to_load
    def delete(self):
        self.delete_button.click().click(label='Delete')
        return self

    @property
    def loaded(self):
        return self.add_ccs_button.wait_until_condition(EC.visibility_of_element_located)


class EditCcPanelBase(CloudCredentials):
    cloud_field = Dropdown(xpath="//input[@name='cloud' and @role='combobox']")
    id_field = Label(xpath="//span[text()='ID']/parent::label/following-sibling::div/div")
    name_field = Input(xpath="//input[@name='name']")
    save_button = Button(xpath="//div[contains(@class, 'x-docked-bottom')]"
                               "//span[contains(@class, 'x-btn-icon-save')]")
    cancel_button = Button(xpath="//div[contains(@class, 'x-docked-bottom')]"
                                 "//span[contains(@class, 'x-btn-icon-cancel')]")
    delete_button = ConfirmButton(xpath="//div[contains(@class, 'x-docked-bottom')]"
                                        "//span[contains(@class, 'x-btn-icon-delete')]")
    loader = Image(xpath="//img[contains(@class, 'x-fieldset-loader')]")

    required_fields = [name_field]

    @property
    def loaded(self):
        with self.driver.implicitly_wait_time(1):
            self.loader.wait_until_condition(EC.invisibility_of_element_located)
        return self.cancel_button.wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def save(self):
        self.save_button.click()
        return self

    def cancel(self):
        self.cancel_button.click()
        return CloudCredentials(self.driver, self.base_url)

    @wait_for_page_to_load
    def delete(self):
        self.delete_button.click().click(label='Delete')
        return CloudCredentials(self.driver, self.base_url)


class EditCcPanelAWS(EditCcPanelBase):
    access_key_id_field = Input(xpath="//input[@name='accessKey']")
    access_key_secret_field = Input(xpath="//input[@name='secretKey']")
    account_type_button_xpath = "//a[contains(@class, 'x-btn')]" \
                                "//span[contains(@class, 'x-btn-button')]" \
                                "/span[text()='%s']"

    # Detailed billing section
    detailed_billing_section = CollapsibleFieldset(header='Enable detailed billing')
    billing_credentials_field = Dropdown(xpath="//input[@name='detailedBillingCredentialsId' and @role='combobox']")
    billing_bucket_region_field = Dropdown(xpath="//input[@name='detailedBillingRegion' and @role='combobox']")
    billing_bucket_name_field = Input(xpath="//input[@name='detailedBillingBucket']")

    # Edit mode
    iam_user_arn_field = Label(xpath="//span[text()='IAM User ARN']/parent::label/following-sibling::div/div")
    cm_tags_grid = CostManagerTagsGrid(xpath="//div[contains(@id, 'cloudcredentialscostmanagercustomtags') "
                                             "and contains(@class, 'x-panel-default')]")

    required_fields = [EditCcPanelBase.name_field,
                       access_key_id_field,
                       access_key_secret_field]

    def fill(self,
             name: str = None,
             access_key_id: str = None,
             access_key_secret: str = None,
             account_type: str = None):
        if name:
            self.name_field.write(name)
        if access_key_id:
            self.access_key_id_field.write(access_key_id)
        if access_key_secret:
            self.access_key_secret_field.write(access_key_secret)
        if account_type:
            account_type_button = Button(driver=self.driver,
                                         xpath=self.account_type_button_xpath % account_type)
            account_type_button.click()
        return self

    def fill_detailed_billing(self,
                              bucket_name: str = None,
                              bucket_region: str = None,
                              credentials: str = None):
        self.detailed_billing_section.expand()
        if bucket_name:
            self.billing_bucket_name_field.write(bucket_name)
        if credentials:
            self.billing_credentials_field.select(credentials)
        if bucket_region:
            self.billing_bucket_region_field.select(bucket_region, exact_match=False)
        return self


class EditCcPanelAzure(EditCcPanelBase):
    account_type_button_xpath = "//a[contains(@class, 'x-btn')]" \
                                "//span[contains(@class, 'x-btn-button')]" \
                                "/span[text()='%s']"
    app_client_id_field = Input(xpath="//input[@name='appClientId']")
    app_secret_key_field = Input(xpath="//input[@name='appSecretKey']")
    continue_button = Button(xpath="//span[contains(@class, 'x-btn-icon-next')]")
    tenant_id_field = Input(xpath="//input[@name='tenantId']")
    advanced_options_section = CollapsibleFieldset(header='Advanced options')

    # Next step
    tenant_id_combo = Dropdown(xpath="//input[@name='tenantId' and @role='combobox']")
    subscription_combo = Dropdown(xpath="//input[@name='subscriptionId' and @role='combobox']")

    detailed_billing_section = CollapsibleFieldset(header='Enable detailed billing')
    cm_tags_grid = CostManagerTagsGrid(xpath="//div[contains(@id, 'cloudcredentialscostmanagercustomtags') "
                                             "and contains(@class, 'x-panel-default')]")

    required_fields = [EditCcPanelBase.name_field,
                       app_client_id_field,
                       app_secret_key_field]

    def fill(self,
             name: str = None,
             account_type: str = None,
             app_client_id: str = None,
             app_secret_key: str = None,
             tenant_id: str = None):
        if name:
            self.name_field.write(name)
        if account_type:
            account_type_button = Button(driver=self.driver,
                                         xpath=self.account_type_button_xpath % account_type)
            account_type_button.click()
        if app_client_id:
            self.app_client_id_field.write(app_client_id)
        if app_secret_key:
            self.app_secret_key_field.write(app_secret_key)
        if tenant_id:
            self.advanced_options_section.expand()
            self.tenant_id_field.write(tenant_id)
        return self

    def enable_detailed_billing(self):
        self.detailed_billing_section.expand()
        return self

    @wait_for_page_to_load
    def next(self):
        self.continue_button.click()
        return self

    def select_subscription(self, value):
        self.subscription_combo.select(option=value, exact_match=False)
        return self


class EditCcPanelCloudstack(EditCcPanelBase):
    api_url_field = Input(xpath="//input[@name='apiUrl']")
    api_key_field = Input(xpath="//input[@name='apiKey']")
    secret_key_field = Input(xpath="//input[@name='secretKey']")

    # Edit mode
    version_field = Label(xpath="//span[text()='Version']/parent::label/following-sibling::div/div")

    required_fields = [EditCcPanelBase.name_field,
                       api_key_field,
                       secret_key_field]

    def fill(self,
             name: str = None,
             api_url: str = None,
             api_key: str = None,
             secret_key: str = None):
        if name:
            self.name_field.write(name)
        if api_url:
            self.api_url_field.write(api_url)
        if api_key:
            self.api_key_field.write(api_key)
        if secret_key:
            self.secret_key_field.write(secret_key)
        return self


class EditCcPanelOpenstack(EditCcPanelBase):
    keystone_url_field = Input(xpath="//input[@name='keystoneUrl']")
    domain_name_field = Input(xpath="//input[@name='domainName']")
    username_field = Input(xpath="//input[@name='username']")
    password_field = Input(xpath="//input[@name='password']")
    tenant_name_field = Input(xpath="//input[@name='tenantName']")
    ssl_verification_checkbox = Checkbox(text='Enable SSL')

    # Edit mode
    regions_active_tab = Label(xpath="(//div[contains(@class, 'x-tabs-flat')]"
                                     "/div[contains(@class, 'x-tab-bar')]"
                                     "//a[contains(@class, 'x-tab-active')]/span/span/span)"
                                     "[last()]")

    required_fields = [EditCcPanelBase.name_field,
                       username_field,
                       password_field,
                       tenant_name_field]

    def fill(self,
             name: str = None,
             keystone_url: str = None,
             username: str = None,
             password: str = None,
             tenant_name: str = None,
             domain_name: str = None,
             ssl_verification: bool = False):
        if name:
            self.name_field.write(name)
        if keystone_url:
            self.keystone_url_field.write(keystone_url)
        if domain_name:
            self.domain_name_field.wait_until_condition(EC.visibility_of_element_located)
            self.domain_name_field.write(domain_name)
        if username:
            self.username_field.write(username)
        if password:
            self.password_field.write(password)
        if tenant_name:
            self.tenant_name_field.write(tenant_name)
        self.ssl_verification_checkbox.checked = ssl_verification
        return self


class EditCcPanelVMware(EditCcPanelBase):
    url_field = Input(xpath="//input[@name='url']")
    username_field = Input(xpath="//input[@name='username']")
    password_field = Input(xpath="//input[@name='password']")
    ssl_verification_checkbox = Checkbox(text='Enable SSL')

    api_version_field = Label(xpath="//span[text()='API Version']/parent::label/following-sibling::div/div")

    detailed_billing_section = CollapsibleFieldset(header='Enable detailed billing')
    cm_tags_grid = CostManagerTagsGrid(xpath="//div[contains(@id, 'cloudcredentialscostmanagercustomtags') "
                                             "and contains(@class, 'x-panel-default')]")

    required_fields = [EditCcPanelBase.name_field,
                       username_field,
                       password_field]

    def fill(self,
             name: str = None,
             url: str = None,
             username: str = None,
             password: str = None,
             ssl_verification: bool = False):
        if name:
            self.name_field.write(name)
        if url:
            self.url_field.write(url)
        if username:
            self.username_field.write(username)
        if password:
            self.password_field.write(password)
        self.ssl_verification_checkbox.checked = ssl_verification
        return self

    @wait_for_page_to_load
    def enable_detailed_billing(self):
        self.detailed_billing_section.expand()
        return self


class EditCcPanelGce(EditCcPanelBase):
    config_type_button_xpath = "//a[contains(@class, 'x-btn')]" \
                               "//span[contains(@class, 'x-btn-button')]" \
                               "/span[text()='%s']"

    project_id_field = Input(xpath="//input[@name='projectId']")
    client_id_field = Input(xpath="//input[@name='clientId']")
    service_acc_email_field = Input(xpath="//input[@name='serviceAccountName']")
    private_key_file = FileInput(xpath="//input[@type='file' and @name='key']")
    private_key_field = Input(xpath="//input[@type='file' and @name='key']"
                                    "/ancestor::div[contains(@id, 'filefield')]//input[@type='text']")
    json_key_file = FileInput(xpath="//input[@type='file' and @name='jsonKey']")
    json_key_field = FileInput(xpath="//input[@type='file' and @name='jsonKey']"
                                     "/ancestor::div[contains(@id, 'filefield')]//input[@type='text']")

    # Detailed billing section
    detailed_billing_section = CollapsibleFieldset(header='Enable detailed billing')
    dataset_name_field = Input(xpath="//input[@name='detailedBillingDatasetName']")
    cm_tags_grid = CostManagerTagsGrid(xpath="//div[contains(@id, 'cloudcredentialscostmanagercustomtags') "
                                             "and contains(@class, 'x-panel-default')]")

    required_fields = [EditCcPanelBase.name_field,
                       project_id_field,
                       client_id_field,
                       service_acc_email_field,
                       private_key_field]

    def fill(self,
             name: str = None,
             config_type: str = None,
             project_id: str = None,
             json_key_path: str = None):
        if name:
            self.name_field.write(name)
        if config_type:
            config_type_button = Button(driver=self.driver,
                                        xpath=self.config_type_button_xpath % config_type)
            config_type_button.click()
        if project_id:
            self.project_id_field.write(project_id)
        if json_key_path:
            self.json_key_file.write(json_key_path)
        return self

    def fill_detailed_billing(self,
                              dataset_name: str = None):
        self.detailed_billing_section.expand()
        if dataset_name:
            self.dataset_name_field.write(dataset_name)
        return self


CC_EDITOR = {
    'AWS': EditCcPanelAWS,
    'Azure': EditCcPanelAzure,
    'Cloudstack': EditCcPanelCloudstack,
    'Openstack': EditCcPanelOpenstack,
    'VMware vSphere': EditCcPanelVMware,
    'Google Compute Engine': EditCcPanelGce
}
