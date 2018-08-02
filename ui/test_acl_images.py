import base64
import re
import os
import time
from pathlib import Path

import pytest
from selenium.common.exceptions import NoSuchElementException

import pages
import elements
from fixtures import testenv


class TestACLImages():
    default_user = 'test@scalr.com'
    default_password = 'EXJx^YqLaI'

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium, testenv):
        self.driver = selenium
        self.container = testenv
        self.login_page = pages.LoginPage(
            self.driver,
            'http://%s.test-env.scalr.com' % self.container.te_id).open()


    def test_create_acl(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        acl_page = acc_dashboard.menu.go_to_acl()
        acl_page.new_acl_button.click()
        acl_page.name_field.write('Selenium')
        acl_page.permissions_filter.write('Images')
        acl_page.get_permission("Import").uncheck()
        acl_page.get_permission(
            "Manage", label="Allows to manage (register/edit/delete) images.").uncheck()
        acl_page.save_button.click()
        message_popup = elements.Label(
            text="ACL successfully saved", driver=acl_page.driver)
        assert message_popup.visible(
            timeout=15), "No message present about successfull saving of the new ACL"

    def test_create_new_user(self):
        ssh = self.container.get_ssh()
        ssh.run("rm -f /opt/scalr-server/libexec/mail/ssmtp")
        for root, dirs, files in os.walk(Path.home()):
            for name in files:
                if name == 'ssmtp':
                    path = os.path.abspath(os.path.join(root, name))
        self.container.put_file(
            path,
            '/opt/scalr-server/libexec/mail/ssmtp')
        ssh.run('chmod 777 /opt/scalr-server/libexec/mail/ssmtp')
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        users_page = acc_dashboard.menu.go_to_users()
        users_page.new_user_button.click()
        users_page.email_field.write('selenium@scalr.com')
        users_page.admin_access_on.click()
        users_page.allow_to_manage_envs_checkbox.check()
        users_page.save_button.click()
        message_popup = elements.Label(
            text="User successfully added and invite sent", driver=users_page.driver)
        assert message_popup.visible(
            timeout=15), "No message present about successfull saving of the new user!"
        table_entry = elements.Label(
            xpath='//table [starts-with(@id, "tableview")]//child::div [contains(text(), "selenium@scalr.com")]',
            driver=users_page.driver)
        assert table_entry.visible(
            timeout=15), "User with email selenium@scalr.com was not found in users table!"

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
        message_popup = elements.Label(
            text="Team successfully saved", driver=teams_page.driver)
        assert message_popup.visible(
            timeout=15), "No message present about successfull saving of the new Team"
        table_entry = elements.Label(
            text="Selenium Team", driver=teams_page.driver)
        assert table_entry.visible(timeout=15), "Selenium Team was not found!"

    def test_new_environment(self):
        env_dashboard = self.login_page.login(
            self.default_user, self.default_password)
        acc_dashboard = env_dashboard.menu.go_to_account()
        env_page = acc_dashboard.menu.go_to_environments()
        env_page.new_env_button.click()
        env_page.env_name_field.write("Selenium Env")
        env_page.cost_center_combobox.select("Default cost centre")
        env_page.link_cloud_to_environment(
            "Google Compute Engine", "global-gce-scalr-labs (PAID)")
        env_page.grant_access("Selenium Team")
        env_page.save_button.click()
        message_popup = elements.Label(
            text="Environment successfully created", driver=env_page.driver)
        assert message_popup.visible(
            timeout=15), "No message present about successfull saving of the new Environment"
        envs = env_page.list_environments()
        assert any(
            "Selenium Env" in env.text for env in envs), "Selenium Env was not found in list!"

    def test_new_user_login(self):
        ssh = self.container.get_ssh()
        out = ssh.run('cat /opt/scalr-server/var/log/unsent-mail/unsent*')[0]
        res = ''.join(out.splitlines()[-18:])
        message = base64.b64decode(''.join(res)).decode("utf-8")
        temp_password = re.search(
            '\\nYour password is: (.+)\\n\\nResources', message).group(1)
        self.login_page.update_password_and_login(
            'selenium@scalr.com', temp_password, 'Scalrtesting123!')

    def test_new_user_images_access(self):
        env_dashboard = self.login_page.login(
            'selenium@scalr.com', 'Scalrtesting123!')
        env_dashboard = env_dashboard.go_to_environment(env_name="Selenium Env")
        env_dashboard.scalr_main_menu.click()
        main_menu_items = env_dashboard.scalr_main_menu.list_items()
        main_menu_items['Images'].mouse_over()
        time.sleep(3)
        assert elements.Button(text="Images Library", driver=self.driver).visible(), "Can't find Images Library in Images sub-menu!"
        assert elements.Button(text="Image Builder", driver=self.driver).visible(), "Can't find Image Builder in Images sub-menu!"
        assert elements.Button(text="Bundle Tasks", driver=self.driver).visible(), "Can't find Bundle Tasks in Images sub-menu!"
        disabled_options = ["Register Existing Image",
                            "Create Image from non-Scalr Server"]
        for option in disabled_options:
            assert elements.Button(text=option, driver=self.driver).hidden(), '%s is present in Images submenu!' % option

    def test_image_builder(self):
        env_dashboard = self.login_page.login(
            'selenium@scalr.com', 'Scalrtesting123!')
        env_dashboard = env_dashboard.go_to_environment(env_name="Selenium Env")
        images_page = env_dashboard.go_to_images()
        builder_page = images_page.image_builder()
        builder_page.create_role("Ubuntu 14.04 Trusty", "test-selenium-image", only_image=True)
