import pytest
import re
import base64

from selenium.common.exceptions import NoSuchElementException

import pages
import elements
from fixtures import testenv


class TestSelenium():
    default_user = 'test@scalr.com'
    default_password = '^Qb?${q8DB'

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        self.container = testenv
        self.login_page = pages.LoginPage(
            self.driver,
            'http://%s.test-env.scalr.com' % self.container.te_id).open()

    def test_create_new_acl(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        acl_page = acc_dashboard.menu.go_to_acl()
        acl_page.new_acl_button.click()
        acl_page.name_field.write('Selenium')
        acl_page.permissions_filter.write('All Farms')
        acl_page.set_access('All Farms', 'No access')
        acl_page.permissions_filter.write('Farms Your Teams Own')
        acl_page.get_permission("Update").uncheck()
        acl_page.save_button.click()
        message_popup = elements.Label(text="ACL successfully saved", driver=acl_page.driver)
        assert message_popup.visible(timeout=15), "No message present about successfull saving of the new ACL"

    def test_create_new_user(self):
        ssh = self.container.get_ssh()
        ssh.run("rm -f /opt/scalr-server/libexec/mail/ssmtp")
        self.container.put_file(
            '/vagrant/revizor/etc/fixtures/resources/scripts/ssmtp',
            '/opt/scalr-server/libexec/mail/ssmtp')
        ssh.run('chmod 777 /opt/scalr-server/libexec/mail/ssmtp')
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        users_page = acc_dashboard.menu.go_to_users()
        users_page.new_user_button.click()
        users_page.email_field.write('selenium@scalr.com')
        users_page.save_button.click()
        message_popup = elements.Label(text="User successfully added and invite sent", driver=users_page.driver)
        assert message_popup.visible(timeout=15), "No message present about successfull saving of the new user!"
        table_entry = elements.Label(
            xpath='//table [starts-with(@id, "tableview")]//child::div [contains(text(), "selenium@scalr.com")]',
            driver=users_page.driver)
        assert table_entry.visible(timeout=15), "User with email selenium@scalr.com was not found in users table!"

    def test_create_new_team(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        teams_page = acc_dashboard.menu.go_to_teams()
        teams_page.new_team_button.click()
        teams_page.team_name_field.write("Selenium Team")
        teams_page.acl_combobox.select('Selenium')
        teams_page.add_user_to_team('selenium@scalr.com')
        teams_page.save_button.click()
        message_popup = elements.Label(text="Team successfully saved", driver=teams_page.driver)
        assert message_popup.visible(timeout=15), "No message present about successfull saving of the new Team"
        table_entry = elements.Label(text="Selenium Team", driver=teams_page.driver)
        assert table_entry.visible(timeout=15), "Selenium Team was not found!"

    def test_new_environment(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        env_page = acc_dashboard.menu.go_to_environments()
        env_page.new_env_button.click()
        env_page.env_name_field.write("Selenium Env")
        env_page.cost_center_combobox.select("Default cost centre")
        env_page.link_cloud_to_environment("Google Compute Engine", "global-gce-scalr-labs (PAID)")
        env_page.grant_access("Selenium Team")
        env_page.save_button.click()
        message_popup = elements.Label(text="Environment successfully created", driver=env_page.driver)
        assert message_popup.visible(timeout=15), "No message present about successfull saving of the new Environment"
        envs = env_page.list_environments()
        assert any("Selenium Env" in env.text for env in envs), "Selenium Env was not found in list!"

    def test_create_farm_from_new_env(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        env_dashboard = env_dashboard.menu.go_to_environment(env_name="Selenium Env")
        farms_page = env_dashboard.menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm" in farms, "Selenium Farm not found!"

    def test_create_farm_for_team(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        env_dashboard = env_dashboard.menu.go_to_environment(env_name="Selenium Env")
        farms_page = env_dashboard.menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm2')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        new_farm_page.teams_dropdown.select("Selenium Team")
        farms_page = new_farm_page.save_farm()
        farms = [farm["name"] for farm in farms_page.list_farms()]
        assert "Selenium Farm2" in farms, "Selenium Farm2 not found!"
        farm = elements.Label(
            xpath='//div [@data-qtip="<span>Selenium Team</span><br/>"]//ancestor::tr/child::td/child::div [contains(text(), "Selenium Farm2")]',
            driver=farms_page.driver)
        assert farm.visible(), "Selenium Farm2 with Selenium Team was not found!"

    def test_new_user_login(self):
        ssh = self.container.get_ssh()
        out = ssh.run('cat /opt/scalr-server/var/log/unsent-mail/unsent*')[0]
        res = ''.join(out.splitlines()[-18:])
        message = base64.b64decode(''.join(res)).decode("utf-8")
        temp_password = re.search('\\nYour password is: (.+)\\n\\nResources', message).group(1)
        self.login_page.update_password_and_login('selenium@scalr.com', temp_password, 'Scalrtesting123!')

    def test_new_user_farms_access(self):
        env_dashboard = self.login_page.login(
            'selenium@scalr.com', 'Scalrtesting123!')
        farms_page = env_dashboard.go_to_farms()
        farms = farms_page.list_farms()
        farm_names = [farm['name'] for farm in farms]
        assert "Selenium Farm" not in farm_names, "selenium@scalr.com user has access to Selenium Farm, but should not!"
        assert "Selenium Farm2" in farm_names, "selenium@scalr.com user has no access to Selenium Farm2!"
        with pytest.raises(NoSuchElementException, message="selenium@scalr.com user can configure Selenium Farm2, but should not!"):
            farm = [farm for farm in farms if farm['name'] == "Selenium Farm2"][0]
            farm['action_menu'].select("Configure")

    def test_create_farm_with_new_user(self):
        env_dashboard = self.login_page.login(
            'selenium@scalr.com', 'Scalrtesting123!')
        farms_page = env_dashboard.menu.go_to_farms()
        new_farm_page = farms_page.new_farm()
        new_farm_page.farm_name_field.write('Selenium Farm3')
        new_farm_page.projects_dropdown.select("Default project / Default cost centre")
        farms_page = new_farm_page.save_farm()
        farm = [farm for farm in farms_page.list_farms() if farm['name'] == "Selenium Farm3"][0]
        assert farm, "Selenium Farm3 not found!"
        farm_designer = farms_page.configure_farm(farm['farm_id'])
        assert isinstance(farm_designer, pages.FarmDesigner), "Unable to open Farm Designer page for Selenium Farm3"
