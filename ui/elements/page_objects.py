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
    """Popup window used to confirm actions.
       Delete objects, reboot, launch or terminate servers, farms.
       Usage example:
       confirm_panel = ConfirmPanel(driver)
       confirm_panel.cancel()
       confirm_panel.delete()
       confirm_panel.launch()
       confirm_panel.terminate.farm()
       confirm_panel.terminate.server()
       confirm_panel.reboot()
    """

    _confirm_types = dict(
        delete='Delete',
        cancel='Cancel',
        launch='Launch',
        terminate={
            'farm': 'OK',
            'server': 'Terminate'
        },
        reboot='Reboot',
    )

    def __init__(self, driver):
        self.driver = driver

    def __getattr__(self, attr):
        self.__dict__.setdefault('attrs', []).append(attr)
        return self

    def __call__(self, *args, **kwargs):
        try:
            confirm_types = self._confirm_types.copy()
            for attr in self.__dict__['attrs']:
                if isinstance(confirm_types.get(attr), str):
                    self._click(confirm_types[attr])
                    return
                confirm_types = confirm_types.pop(attr, dict())
            raise NoSuchAttributeException(
                f"Can not be called: \"{'.'.join(self.__dict__['attrs'])}()\", element attributes does not defined.")
        finally:
            del self.__dict__['attrs']

    def _click(self, label):
        """Confirm or cancel action
        """
        xpath = f"(//div [contains(@class, 'x-panel-confirm')])[1]//following::span [text()='{label}']"
        self.driver.find_element_by_xpath(xpath).click()
