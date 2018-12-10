import time

from selenium.webdriver.common.action_chains import ActionChains

from elements import locators
from elements.base import Button


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


class ConfirmPopup(object):
    """Popup window opened to confirm delete element,
    """
    def __init__(self, driver):
        self.driver = driver
