import pytest
import uuid
import time

from selenium.webdriver.support.ui import WebDriverWait
import pages


class TestCase():

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium):
        self.driver = selenium
        self.wait = WebDriverWait(self.driver, 30)
        self.test_id = uuid.uuid1()
        self.login_page = pages.LoginPage(self.driver, 'http://c4dba9c8bdbf.test-env.scalr.com').open()
        self.env_dashboard = self.login_page.login('test@scalr.com', '^Qb?${q8DB')
        yield
        self.driver.save_screenshot("/vagrant/ui/acl_%s.png" % self.test_id)
        self.env_dashboard = pages.EnvironmentDashboard(self.driver, 'http://c4dba9c8bdbf.test-env.scalr.com').open()

    def test_create_new_acl(self):
        acc_dashboard = self.env_dashboard.go_to_account()
        acl_page = acc_dashboard.go_to_acl()
        acl_page.new_acl()
        acl_page.new_acl_name_field.send_keys('test-%s' % self.test_id)
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
        pass
