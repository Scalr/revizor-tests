import time
import logging

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchAttributeException

from elements import locators
from elements.base import Button

LOG = logging.getLogger()


class LeftPopupMenu:

    def __init__(self, driver):
        self.driver = driver
        self.main_button = Button(
            icon='el-default-toolbar-small x-scalr-icon', driver=self.driver)

    def _convert_elements(self, elements):
        items = {}
        for element in elements:
            if element.text and element.text.strip() not in items.keys():
                items[element.text.strip()] = Button(
                    element_id=element.get_attribute("id"), driver=self.driver)
        return items

    def click(self):
        return self.main_button.click()

    def scroll(self, direction):
        chain = ActionChains(self.driver)
        if direction == "down":
            scroller_id = "after"
        elif direction == "up":
            scroller_id = "before"
        else:
            raise ValueError(
                "Scrolling direction must be 'down' or 'up', not %s!" % direction)
        for _ in range(10):
            scroller = Button(
                xpath='//div [starts-with(@id, "menu") and contains(@id, "%s-scroller")]' % scroller_id,
                driver=self.driver).get_element()
            if 'x-box-scroller-disabled' not in scroller.get_attribute('class'):
                print("Scrolling %s" % direction)
                chain.click_and_hold(scroller)
                chain.perform()
                time.sleep(1)
            else:
                chain.reset_actions()
                chain.release()
                chain.perform()
                break

    def list_items(self):
        LOG.debug('List items in Scalr main (left) menu.')
        self.scroll("up")
        upper_elements = Button(
            xpath='//div [contains(@class, "x-topmenu-dropdown")]//child::a [@role="menuitem"]',
            driver=self.driver).list_elements(show_hidden=True)
        items = self._convert_elements(upper_elements)
        self.scroll("down")
        lower_elements = Button(
            xpath='//div [contains(@class, "x-topmenu-dropdown")]//child::a [@role="menuitem"]',
            driver=self.driver).list_elements(show_hidden=True)
        items.update(self._convert_elements(lower_elements))
        return items

    def select(self, option):
        LOG.debug('Select "%s" from Scalr main menu.' % option)
        option = option.split('>')
        main_option = option[0].strip()
        sub_option = option[1].strip() if len(option) > 1 else None
        item = self.list_items()[main_option]
        if item.hidden():
            item.scroll_into_view()
        if sub_option:
            item.mouse_over()
            Button(
                xpath='//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % sub_option,
                driver=self.driver).click()
        else:
            return item.click()


class ConfirmPanel(object):

    _element = None

    def __init__(self, driver):
        self.driver = driver

    @property
    def _panel(self):
        if not self._element:
            for element in self.driver.find_elements_by_xpath("//div [contains(@class, 'x-panel-confirm')]"):
                if 'x-panel-confirm' in element.get_attribute('class').split():
                    self._element = element
        return self._element

    def click_by_label(self, label):
        element = self._panel.find_element_by_xpath(f"./descendant::* [text()='{label}']")
        element.click()


class ConfirmButton(Button):
    """Implements the element click on which requires confirmation of actions. Delete object, terminate farm, servers etc...
    """
    def click(self):
        LOG.debug(f'Click button  with confirmed action: {str(self.locator)}')
        self.get_element().click()
        return ConfirmPanel(driver=self.driver)



