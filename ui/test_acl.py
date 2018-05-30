import pytest
import uuid
import time

from selenium.webdriver.support.ui import WebDriverWait
import ui.pages as pages


class TestAcl():

    @pytest.fixture(autouse=True)
    def prepare_env(self, selenium):
        self.driver = selenium
        self.wait = WebDriverWait(self.driver, 30)
        yield
        self.driver.save_screenshot("/vagrant/ui/acl_%s.png" % uuid.uuid1())

    def test_create_new_acl(self):
        login_page = pages.LoginPage(self.driver, 'http://c4dba9c8bdbf.test-env.scalr.com').open()
        env_dashboard = login_page.login('test@scalr.com', '^Qb?${q8DB')
        acc_dashboard = env_dashboard.go_to_account()
        acl_page = acc_dashboard.go_to_acl()
        acl_page.new_acl()
        acl_page.new_acl_name_field.send_keys('test-this-shit')
        acl_page.new_acl_permissions_filter.send_keys('All Farms')
        acl_page.set_access('All Farms', 'No access')
        acl_page.new_acl_permissions_filter.clear()
        acl_page.new_acl_permissions_filter.send_keys('Farms Your Teams Own')
        time.sleep(5)
        acl_page.click_checkbox_option("Update", action="uncheck")
