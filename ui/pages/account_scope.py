import typing as tp

from selenium.webdriver.support import expected_conditions as EC

from elements.base import Button, Label, Input, SearchInput, Menu, Checkbox, Combobox, Table, TableRow, SplitButton
from elements.page_objects import ConfirmButton
from pages.base import wait_for_page_to_load
from pages.common import CommonTopMenu
from pages.global_scope import EditCcPanelBase, CC_EDITOR


class AccountTopMenu(CommonTopMenu):

    @wait_for_page_to_load
    def go_to_acl(self):
        """Redirects to ACL page (Account scope).
           Returns ACL page object.
        """
        Button(href="#/account/acl", driver=self.driver).click()
        return ACL(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_users(self):
        """Redirects to Users page (Account scope).
           Returns Users page object.
        """
        Button(href="#/account/users", driver=self.driver).click()
        return Users(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_teams(self):
        """Redirect to Teams page (Account scope).
           Returns Teams page object.
        """
        Button(href="#/account/teams", driver=self.driver).click()
        return Teams(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_scripts(self):
        """Redirect to Scripts page (Account scope).
           Returns Scripts page object.
        """
        Button(href="#/account/scripts", driver=self.driver).click()
        return Scripts(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_environments(self):
        """Redirects to Environments page (Account scope).
           Returns Environments page object.
        """
        Button(href="#/account/environments",
               driver=self.driver).click()
        return Environments(self.driver, self.base_url)


class AccountLeftMenu(CommonTopMenu):

    def go_to_roles(self):
        """Redirects to Roles page (list of Scalr roles).
           Returns Roles page object.
        """
        from pages.roles import Roles
        Button(xpath="//a[@role='menuitem']/span[.='Roles Library']", driver=self.driver).click()
        return Roles(self.driver, self.base_url)

    def go_to_policy_groups(self):
        """Redirects to Policy Groups page (list of Scalr polies).
           Returns Policy Groups page object.
        """
        Button(xpath="//a[@role='menuitem']/span[.='Policy Groups']", driver=self.driver).click()
        return PolicyGroups(self.driver, self.base_url)

    @wait_for_page_to_load
    def go_to_cloud_credentials(self) -> 'CloudCredentials':
        """Redirects to Cloud Credentials page (Account scope).
           Returns CloudCredentials page object.
        """
        self.scope_main_menu.click()
        self.scope_main_menu.select("Cloud Credentials")
        return CloudCredentials(self.driver, self.base_url)


class AccountDashboard(AccountTopMenu, AccountLeftMenu):
    URL_TEMPLATE = '/#/account/dashboard'
    accounts_menu_btn = Button(xpath="//a [contains(@class, 'x-btn-environment')]"
                                     "//descendant::span[contains(@class, 'x-icon-environment')]")

    @property
    def loaded(self):
        return Label(
            "Environments in this account",
            driver=self.driver).wait_until_condition(EC.visibility_of_element_located)

    @wait_for_page_to_load
    def change_environment(self, env_name):
        """Switches to specific Scalr environment.
           Returns EnvironmentDashboard page object.
        """
        env_btn = Button(text=env_name, driver=self.driver)
        self.accounts_menu_btn.click()
        env_btn.wait_until_condition(EC.element_to_be_clickable)
        env_btn.click()
        from pages.environment_scope import EnvironmentDashboard
        return EnvironmentDashboard(self.driver, self.base_url)


class ACL(AccountTopMenu):
    """ACL page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/acl'
    new_acl_button = Button(text="New ACL")
    name_field = Input(label="ACL name")
    permissions_filter = SearchInput(label="Permissions")
    save_button = Button(icon="save")

    @property
    def loaded(self):
        return self.new_acl_button.wait_until_condition(EC.visibility_of_element_located)

    def set_access(self, access_for, access_type):
        """Set specified access level for specified Scalr property.

           :param str access_for: name of the Scalr property.
           :param str access_type: desired access level (Full Access/Limited/Read Only/ No Access).
        """
        menu = Menu(label=access_for, driver=self.driver)
        menu.select(access_type)

    def get_permission(self, name, label=None):
        """Returns Checkbox object for specific permission.

           :param str name: Name(text) of the permission.
        """
        if label:
            return Checkbox(
                xpath='//* [contains(text(), "%s")]//parent::* [@data-value="%s"]' % (
                    label, name.lower()),
                driver=self.driver)
        else:
            return Checkbox(value=name, driver=self.driver)


class Users(AccountTopMenu):
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


class Teams(AccountTopMenu):
    """Teams page from Account scope.
    """
    URL_TEMPLATE = '/#/account/teams'
    new_team_button = Button(text="New team")
    team_name_field = Input(name="name")
    acl_combobox = Combobox(text="Default ACL")
    save_button = Button(icon="save")
    add_members_button = Button(text="Add members")
    select_members_button = Button(text="Select")

    @property
    def loaded(self):
        return self.new_team_button.wait_until_condition(EC.visibility_of_element_located)

    def add_user_to_team(self, email):
        """Adds specified User to currently selected Team.

           :param str email: user email.
        """
        self.add_members_button.click()
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::div[@class="x-grid-row-checker"]' % email
        Button(xpath=xpath, driver=self.driver).click()
        return self.select_members_button.click()

    def remove_user_from_team(self, email):
        """Removes specified User from currently selected Team.

           :param str email: user email.
        """
        xpath = '//*[contains(text(), "%s")]//ancestor::tr[@class="  x-grid-row"]//child::a[@data-qtip="Remove from team"]' % email
        return Button(xpath=xpath, driver=self.driver).click()


class Environments(AccountTopMenu):
    """Environments page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/environments'
    new_env_button = Button(text="New environment")
    env_name_field = Input(name="name")
    cost_center_combobox = Combobox(
        xpath='//span[contains(text(), "Cost center")]//ancestor::label//following-sibling::div[starts-with(@id, "combobox")]',
        span=False)
    access_tab = Button(text="Access")
    grant_access_menu = Button(text="Grant access")
    grant_access_button = Button(
        xpath='//span [contains(text(), "Grant access")]//ancestor::a[@class="x-btn x-unselectable x-box-item x-btn-default-small"]')
    save_button = Button(icon="save")
    active_envs = Label(
        xpath='//div[starts-with(@class, "x-dataview-tab")]')
    policies_tab = Button(xpath="//a[.='Policies']")

    @property
    def loaded(self):
        return self.new_env_button.wait_until_condition(EC.visibility_of_element_located)

    def link_cloud_to_environment(self, cloud_name, credentials_name):
        """Links cloud (by cloud name) to currently selected Scalr Environment
           with specified Scalr credentials.

           :param str cloud_name: Cloud name (abbreviation) as it's displayed in Scalr UI.
           :param str credentials_name: name of the cloud credentials.
        """
        cloud_button = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % cloud_name,
            driver=self.driver)
        credentials = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table' % credentials_name,
            driver=self.driver)
        link_button = Button(
            text="Link to Environment", driver=self.driver)
        cloud_button.click()
        credentials.click()
        link_button.click()

    def link_policies_to_environment(self, policy_type, policy_group):
        """Links Policies (by policy type name) to currently selected Scalr Environment
           with specified Scalr policy groups.

           :param str policy_type: Policy type name (abbreviation) as it's displayed in Scalr UI.
           :param str policy_group: name of the Policy groups.
        """
        policy_type_button = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table//child::a' % policy_type,
            driver=self.driver)
        group = Button(
            xpath='//div [contains(text(), "%s")]//ancestor::table' % policy_group,
            driver=self.driver)
        link_button = Button(
            text="Link to Environment", driver=self.driver)
        policy_type_button.click()
        group.click()
        link_button.click()

    def linked_policy_group(self, policy_group_name):
        group = Button(
            text=policy_group_name, driver=self.driver)
        return group

    def grant_access(self, team):
        """Grant access to currently selected Scalr Environment to specified Scalr team.

           :param str team: Scalr team name.
        """
        self.access_tab.click()
        self.grant_access_menu.click()
        team_checkbox = Checkbox(
            xpath='//div [contains(text(), "%s")]//parent::td//parent::tr//child::td//child::div[@class="x-grid-row-checker"]' % team,
            driver=self.driver)
        team_checkbox.check()
        self.grant_access_button.click()

    def list_environments(self):
        """Returns list of Elements of available Scalr Environments.
        """
        return self.active_envs.list_elements()

    def select_active_environment(self, env_name):
        """ Switch to Scalr Environment by Env name.
            Env names example: ' acc1env1', ' acc1env2', ' acc1env1' ...
        """
        env = Button(xpath="//td[.='%s']" % env_name, driver=self.driver)
        env.click()


class Scripts(AccountTopMenu):
    """Scripts page from Account scope.
    """
    URL_TEMPLATE = '/#/account/scripts'
    new_script_button = Button(text="New Scalr script")
    script_name_field = Input(name="name")
    tags_field = Input(name="tags")
    script_content_field_activation = Button(css="div.CodeMirror-scroll")
    script_content_field = Input(css="textarea")
    body_container = Button(xpath="//div[@id='body-container']")
    save_button = Button(icon="save")
    tooltip_policy_tag_not_allowed = Button(
        xpath="//div[@role='alert'][.='Policy Tags are not allowed.']")


class PolicyGroups(AccountLeftMenu):
    """Policy Groups page from Account Scope.
    """
    URL_TEMPLATE = '/#/account/policyengine/groups'
    new_policy_group_button = Button(text="New policy group")
    new_policy_button = Button(xpath="//span[.='New policy'][@data-ref='btnInnerEl']")
    name_field = Input(name="name")
    group_type_combobox = Combobox(xpath="//input[@role='combobox'][@name='type']", span=False)
    policy_type_combobox = Combobox(
        css=".x-picker-field.x-form-item-no-label .x-form-required-field", li=False)
    role_tag_combobox = Combobox(
        css=".x-anchor-form-item:nth-of-type(4) .x-form-text-default", span=False)
    new_policy_ok_button = Button(xpath="//span[contains(text(), 'OK')]")
    chef_servers_checkbox = Button(css=".x-grid:nth-of-type(10) [tabindex='0'] .x-column-header-text")
    save_button = Button(icon="save")
    tooltip_policy_group_saved = Button(
        xpath="//div[.='Policy Group successfully saved'][@class='x-component x-box-item x-component-default']")

    @property
    def loaded(self):
        return self.new_policy_group_button.wait_until_condition(EC.visibility_of_element_located, timeout=13)


class CloudCredentials(AccountTopMenu):
    """Cloud Credentials page from Account scope
    """
    URL_TEMPLATE = '/#/account/credentials'
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
    select_scope_button = SplitButton(xpath="//a[starts-with(@id, 'cyclealt')]")

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

    def switch_scope(self, scope: str):
        self.select_scope_button.click(scope)

    @property
    def loaded(self):
        return self.add_ccs_button.wait_until_condition(EC.visibility_of_element_located)
