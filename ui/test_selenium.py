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
        acl_page.new_acl_button.click()
        acl_page.name_field.write('Selenium')
        acl_page.permissions_filter.write('All Farms')
        time.sleep(3)
        acl_page.set_access('All Farms', 'No access')
        acl_page.permissions_filter.write('Farms Your Teams Own')
        time.sleep(3)
        acl_page.get_permission("Update").uncheck()
        acl_page.save_button.click()
        message_popup = pages.Label(acl_page.driver, text="ACL successfully saved")
        assert message_popup.displayed(timeout=15), "No message present about successfull saving of the new ACL"

    def test_create_new_user(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        users_page = acc_dashboard.go_to_users()
        users_page.new_user_button.click()
        users_page.email_field.write('selenium@scalr.com')
        users_page.save_button.click()
        message_popup = pages.Label(users_page.driver, text="User successfully added and invite sent")
        assert message_popup.displayed(timeout=15), "No message present about successfull saving of the new user!"
        table_entry = pages.Label(
            users_page.driver,
            xpath='//table [starts-with(@id, "tableview")]//child::div [contains(text(), "selenium@scalr.com")]')
        assert table_entry.displayed(timeout=15), "User with email selenium@scalr.com was not found in users table!"

    def test_create_new_team(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        teams_page = acc_dashboard.go_to_teams()
        teams_page.new_team_button.click()
        teams_page.team_name_field.write("Selenium Team")
        teams_page.acl_combobox.select('Selenium')
        teams_page.add_user_to_team('selenium@scalr.com')
        teams_page.save_button.click()
        message_popup = pages.Label(teams_page.driver, text="Team successfully saved")
        assert message_popup.displayed(timeout=15), "No message present about successfull saving of the new Team"
        table_entry = pages.Label(teams_page.driver, text="Selenium Team")
        assert table_entry.displayed(timeout=15), "Selenium Team was not found!"

    def test_new_environment(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        env_page = acc_dashboard.go_to_environments()
        env_page.new_env_button.click()
        env_page.env_name_field.write("Selenium Env")
        env_page.cost_center_combobox.select("Default cost centre")
        env_page.link_cloud_to_environment("Google Compute Engine", "global-gce-scalr-labs (PAID)")
        env_page.grant_access("Selenium Team")
        env_page.save_button.click()
        message_popup = pages.Label(env_page.driver, text="Environment successfully created")
        assert message_popup.displayed(timeout=15), "No message present about successfull saving of the new Environment"
        envs = env_page.list_environments()
        assert any("Selenium Env" in env.text for env in envs), "Selenium Env was not found in list!"

    def test_create_farm_from_new_env(self):
        env_dashboard = self.env_dashboard.go_to_environment(env_name="Selenium Env")
        farms_page = env_dashboard.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm" in farms, "Selenium Farm not found!"

    def test_create_farm_for_team(self):
        env_dashboard = self.env_dashboard.go_to_environment(env_name="Selenium Env")
        farms_page = env_dashboard.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm2')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        new_farm_page.teams_dropdown.select("Selenium Team")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm2" in farms, "Selenium Farm2 not found!"
        farm = pages.Label(
            farms_page.driver,
            xpath='//div [@data-qtip="<span>Selenium Team</span><br/>"]//ancestor::tr/child::td/child::div [contains(text(), "Selenium Farm2")]')
        assert farm.displayed(), "Selenium Farm2 with Selenium Team was not found!"
