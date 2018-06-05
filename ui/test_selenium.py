import pytest
import uuid
import time

from selenium.webdriver.support.ui import WebDriverWait
import pages


class TestSelenium():

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium):
        self.driver = selenium
        self.wait = WebDriverWait(self.driver, 30)
        self.login_page = pages.LoginPage(self.driver, 'http://c9b03eda2ed0.test-env.scalr.com').open()
        self.env_dashboard = self.login_page.login('test@scalr.com', '^Qb?${q8DB')
        yield
        self.driver.save_screenshot("/vagrant/ui/acl_%s.png" % uuid.uuid1())

    def test_create_new_acl(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        acl_page = acc_dashboard.go_to_acl()
        acl_page.new_acl()
        acl_page.new_acl_name_field.send_keys('Selenium')
        acl_page.new_acl_permissions_filter.send_keys('All Farms')
        acl_page.set_access('All Farms', 'No access')
        acl_page.new_acl_permissions_filter.clear()
        acl_page.new_acl_permissions_filter.send_keys('Farms Your Teams Own')
        acl_page.click_checkbox_option("Update", action="uncheck")
        acl_page.save_acl()
        message_popup = self.wait.until(
            lambda d: d.find_elements(*('xpath', '//* [contains(text(), "ACL successfully saved")]')))
        assert message_popup, "No message present about successfull saving of the new ACL"

    def test_create_new_user(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        users_page = acc_dashboard.go_to_users()
        users_page.new_user()
        users_page.new_user_email_field.send_keys('selenium@scalr.com')
        users_page.save_new_user()
        message_popup = self.wait.until(
            lambda d: d.find_elements(*('xpath', '//* [contains(text(), "User successfully added and invite sent")]')))
        assert message_popup, "No message present about successfull saving of the new user!"
        table_entry_locator = ('xpath', '//table [starts-with(@id, "tableview")]//child::div [contains(text(), "selenium@scalr.com")]')
        table_entry = self.wait.until(
            lambda d: d.find_elements(*table_entry_locator))
        assert table_entry, "User with email selenium@scalr.com was not found in users table!"

    def test_create_new_team(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        teams_page = acc_dashboard.go_to_teams()
        teams_page.new_team()
        teams_page.new_team_name_field.send_keys("Selenium Team")
        teams_page.select_default_acl('Selenium')
        teams_page.add_user_to_team('selenium@scalr.com')
        teams_page.save_team()
        message_popup = self.wait.until(
            lambda d: d.find_elements(*('xpath', '//* [contains(text(), "Team successfully saved")]')))
        assert message_popup, "No message present about successfull saving of the new Team"
        table_entry_locator = ('xpath', '//div[contains(text(), "Selenium Team")]//ancestor::table')
        table_entry = self.wait.until(
            lambda d: d.find_elements(*table_entry_locator))
        assert table_entry, "Selenium Team was not found!"

    def test_new_environment(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        env_page = acc_dashboard.go_to_environments()
        env_page.new_environment()
        env_page.new_environment_name_field.send_keys("Selenium Env")
        env_page.select_cost_center("Default cost centre")
        env_page.link_cloud_to_environment("Google Compute Engine", "global-gce-scalr-labs (PAID)")
        env_page.grant_access("Selenium Team")
        env_page.save_environment()
        message_popup = self.wait.until(
            lambda d: d.find_elements(*('xpath', '//* [contains(text(), "Environment successfully created")]')))
        assert message_popup, "No message present about successfull saving of the new Environment"
        envs = env_page.list_environments()
        assert any("Selenium Env" in env for env in envs), "Selenium Env was not found in list!"

    def test_create_new_farm_from_new_env(self):
        env_dashboard = self.env_dashboard.go_to_environment(env_name="Selenium Env")
        farms_page = env_dashboard.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.send_keys('Selenium Farm')
        new_farm_page.select_project("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm" in farms, "Selenium Farm not found!"
