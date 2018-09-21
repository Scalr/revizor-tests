import pytest
import re
import os
import base64
import time

from selenium.common.exceptions import NoSuchElementException

from revizor2.conf import CONF
from pages.login import LoginPage
from pages.environment_scope import FarmDesigner
from elements import locators
from elements.base import Label, Button

DEFAULT_USER = CONF.credentials.testenv.accounts.default['username']
DEFAULT_PASSWORD = CONF.credentials.testenv.accounts.default['password']


class TestACL:

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        self.driver.implicitly_wait(10)
        self.container = testenv
        login_page = LoginPage(
            self.driver,
            'http://%s.test-env.scalr.com' % self.container.te_id).open()
        self.env_dashboard = login_page.login(DEFAULT_USER, DEFAULT_PASSWORD)

    def test_create_new_acl(self):
        acl_page = self.env_dashboard.menu.go_to_account().menu.go_to_acl()
        acl_page.new_acl_button.click()
        acl_page.name_field.write('Selenium')
        acl_page.permissions_filter.write('All Farms')
        acl_page.set_access('All Farms', 'No access')
        acl_page.permissions_filter.write('Farms Your Teams Own')
        acl_page.get_permission("Update").uncheck()
        acl_page.permissions_filter.write('Images')
        acl_page.get_permission("Import").uncheck()
        acl_page.get_permission(
            "Manage", label="Allows to manage (register/edit/delete) images.").uncheck()
        acl_page.save_button.click()
        assert acl_page.page_message.text == "ACL successfully saved", "No message present about successfull saving of the new ACL"

    def test_create_new_user(self, mock_ssmtp):
        users_page = self.env_dashboard.menu.go_to_account().menu.go_to_users()
        users_page.new_user_button.click()
        users_page.email_field.write('selenium@scalr.com')
        users_page.save_button.click()
        assert users_page.page_message.text == "User successfully added and invite sent", "No message present about successfull saving of the new user!"
        table_entry = Label(
            xpath='//table [starts-with(@id, "tableview")]//child::div [contains(text(), "selenium@scalr.com")]',
            driver=users_page.driver)
        assert table_entry.visible(), "User with email selenium@scalr.com was not found in users table!"

    def test_create_new_team(self):
        teams_page = self.env_dashboard.menu.go_to_account().menu.go_to_teams()
        teams_page.new_team_button.click()
        teams_page.team_name_field.write("Selenium Team")
        teams_page.acl_combobox.select('Selenium')
        teams_page.add_user_to_team('selenium@scalr.com')
        teams_page.save_button.click()
        assert teams_page.page_message.text == "Team successfully saved", "No message present about successfull saving of the new Team"
        table_entry = Label(text="Selenium Team", driver=teams_page.driver)
        assert table_entry.visible(), "Selenium Team was not found!"

    def test_create_new_environment(self):
        env_page = self.env_dashboard.menu.go_to_account().menu.go_to_environments()
        env_page.new_env_button.click()
        env_page.env_name_field.write("Selenium Env")
        env_page.cost_center_combobox.select("Default cost centre")
        env_page.link_cloud_to_environment("Google Compute Engine", "global-gce-scalr-labs (PAID)")
        env_page.grant_access("Selenium Team")
        env_page.save_button.click()
        assert env_page.page_message.text == "Environment successfully created", "No message present about successfull saving of the new Environment"
        envs = env_page.list_environments()
        assert any("Selenium Env" in env.text for env in envs), "Selenium Env was not found in list!"

    def test_create_farm_from_new_env(self):
        farms_page = self.env_dashboard.menu.go_to_environment(
            env_name="Selenium Env").menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm" in farms, "Selenium Farm not found!"

    def test_create_farm_for_team(self):
        farms_page = self.env_dashboard.menu.go_to_environment(
            env_name="Selenium Env").menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm2')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        new_farm_page.teams_dropdown.select("Selenium Team")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm2" in farms, "Selenium Farm2 not found!"
        farm = Label(
            xpath='//div [@data-qtip="<span>Selenium Team</span><br/>"]//ancestor::tr/child::td/child::div [contains(text(), "Selenium Farm2")]',
            driver=farms_page.driver)
        assert farm.visible(), "Selenium Farm2 with Selenium Team was not found!"

    def test_new_user_login(self):
        ssh = self.container.get_ssh()
        out = ssh.run('cat /opt/scalr-server/var/log/unsent-mail/unsent*')[0]
        res = ''.join(out.splitlines()[-18:])
        message = base64.b64decode(''.join(res)).decode("utf-8")
        temp_password = re.search('\\nYour password is: (.+)\\n\\nResources', message).group(1)
        login_page = self.env_dashboard.menu.logout()
        login_page.update_password_and_login('selenium@scalr.com', temp_password, 'Scalrtesting123!')
        global DEFAULT_USER
        DEFAULT_USER = 'selenium@scalr.com'
        global DEFAULT_PASSWORD
        DEFAULT_PASSWORD = 'Scalrtesting123!'

    def test_new_user_farms_access(self):
        farms_page = self.env_dashboard.go_to_farms()
        farms = farms_page.list_farms()
        farm_names = [farm['name'] for farm in farms]
        assert "Selenium Farm" not in farm_names, "selenium@scalr.com user has access to Selenium Farm, but should not!"
        assert "Selenium Farm2" in farm_names, "selenium@scalr.com user has no access to Selenium Farm2!"
        with pytest.raises(NoSuchElementException, message="selenium@scalr.com user can configure Selenium Farm2, but should not!"):
            farm = [farm for farm in farms if farm['name'] == "Selenium Farm2"][0]
            farm['action_menu'].select("Configure")

    def test_create_farm_with_new_user(self):
        new_farm_page = self.env_dashboard.menu.go_to_farms().new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm3')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farm = [farm for farm in farms_page.list_farms() if farm['name'] == "Selenium Farm3"][0]
        assert farm, "Selenium Farm3 not found!"
        farm_designer = farms_page.configure_farm(farm['farm_id'])
        assert isinstance(farm_designer, FarmDesigner), "Unable to open Farm Designer page for Selenium Farm3"

    def test_new_user_images_access(self):
        self.env_dashboard.scalr_main_menu.click()
        main_menu_items = self.env_dashboard.scalr_main_menu.list_items()
        main_menu_items['Images'].mouse_over()
        time.sleep(3)
        assert Button(text="Images Library", driver=self.driver).visible(), "Can't find Images Library in Images sub-menu!"
        assert Button(text="Image Builder", driver=self.driver).visible(), "Can't find Image Builder in Images sub-menu!"
        assert Button(text="Bundle Tasks", driver=self.driver).visible(), "Can't find Bundle Tasks in Images sub-menu!"
        disabled_options = ["Register Existing Image",
                            "Create Image from non-Scalr Server"]
        for option in disabled_options:
            assert Button(text=option, driver=self.driver).hidden(), '%s is present in Images submenu!' % option

    def test_create_image_with_builder(self):
        images_page = self.env_dashboard.go_to_images()
        builder_page = images_page.image_builder()
        builder_page.create_role(
            "Ubuntu 14.04 Trusty", "test-selenium-image", only_image=True)
        # Blocked by SCALRCORE-9383
