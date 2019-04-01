import logging
import re
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from elements import locators
from elements.base import Button, Checkbox, Input, Container, Label

LOG = logging.getLogger()


class LeftPopupMenu:

    def __init__(self, driver):
        self.driver = driver
        self.main_button = Button(
            icon='el-default-toolbar-small x-scalr-icon', driver=self.driver)
        self.search_field = Input(
            xpath=".//*[@placeholder='Menu filter']", driver=self.driver)

    def _convert_elements(self, elements):
        items = {}
        for element in elements:
            if element.text and element.text.strip() not in items.keys():
                items[element.text.strip()] = Button(
                    element_id=element.get_attribute("id"), driver=self.driver)
        return items

    def click(self):
        return self.main_button.click()

    def search_field_left_menu(self):
        return self.search_field

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
    """Implements a two kinds of panels: Form or Panel
       Panel type is set when declaring an element
    """

    _panel = None

    def __init__(self, driver, panel_type=None):
        """
        :type panel_type: string
        :param panel_type: panel or form. default panel. parameter depends on the value of the id attribute
        of the returned panel which can be form-{int} or panel-{in}
        Example: <div id="form-1234"> or <div id="panel-1234">
        """
        self.driver = driver
        panel_type = panel_type or 'panel'
        self.locator = locators.XpathLocator(
            f"(//body/div [contains(@class, 'x-panel-confirm')]"
            f"[contains(@id, '{panel_type}')])"
            f"[last()]")

    def get_element(self):
        if not self._panel:
            self._panel = self.driver.find_element(*self.locator)
        return self._panel

    def click(self, label=None, hint=None):
        if label:
            xpath = f"./descendant::* [text()='{label}']"
        elif hint:
            xpath = f"./descendant::* [contains(@data-qtip, '{hint}')]"
        else:
            raise ValueError("Not enough required parameters. 'label' or 'hint' must present.")
        button = self.get_element().find_element_by_xpath(xpath)
        button.click()

    def wait_presence_of(self, timeout=3):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.locator))

    def find_descendant_element(self, xpath):
        """Search for elements inside the confirm panel. The root of search is confirm panel.

        Xpath example: passed xpath='input [@class=class_atr]' for finding input element on panel will be transform to
        '{panel locator}./descendant::input [@class=class_atr]'
        """
        xpath = re.sub(r"^[/]+", '', xpath)
        panel = self.get_element()
        return panel.find_element_by_xpath(''.join(('./descendant::', xpath)))


class ConfirmButton(Button):
    """An accessorial element. Implements the element click on which requires
    confirmation of actions. Delete object, terminate farm, servers etc...
    """

    def click(self, panel_type=None):
        """
        :type panel_type: string
        :param panel_type: panel or form. default panel. parameter depends on the value of the id attribute
        of the returned panel which can be form-{int} or panel-{in}
        Example: <div id="form-1234"> or <div id="panel-1234">
        :return ConfirmPanel element
        """
        LOG.debug(f'Click button  with confirmed action: {str(self.locator)}')
        self.get_element().click()
        return ConfirmPanel(driver=self.driver, panel_type=panel_type)


class GlobalScopeSwitchButton(Checkbox):

    def _make_locator(self, text=None, **kwargs):
        if not text:
            raise ValueError('No toggle text was provided')
        self.locator = locators.XpathLocator(
            f"//* [text()='{text}']"
            f"/ancestor::div[contains(@id, 'togglefield')]")

    @property
    def checked(self):
        element = self.get_element()
        element_class = element.get_attribute('class').split()
        return 'x-form-cb-checked' in element_class

    def _click(self):
        label = self.get_element()
        button = label.find_element_by_xpath("./descendant::input[1]")
        button.click()

    def check(self):
        if not self.checked:
            self._click()

    def uncheck(self):
        if self.checked:
            self._click()


class CostManagerTagsGrid(Container):
    toggle_path = './/table[@class="x-grid-item"]//tr/td[2]/div[text()="%s"]' \
                  '/ancestor::tr/td[1]//div[contains(@class, "x-togglestatuscolumn")]'

    def _make_locator(self, xpath=None):
        if xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    @property
    def header(self):
        path = self.locator[1] + "/div[contains(@class, 'x-toolbar-docked-top')]" \
                                 "//div[contains(@class, 'x-fieldset-subheader')]"
        return Label(driver=self.driver,
                     xpath=path)

    @property
    def _refresh_tags_button(self):
        path = self.locator[1] + "/div[contains(@class, 'x-toolbar-docked-top')]" \
                                 "//a[@data-qtip='Refresh tag list']"
        return Button(driver=self.driver,
                      xpath=path)

    def refresh(self):
        self._refresh_tags_button.click()
        return self

    @property
    def tags(self):
        path = './/table[@class="x-grid-item"]//tr/td[2]/div'
        tags = self.get_element().find_elements_by_xpath(path)
        return [t.get_attribute('textContent') for t in tags]

    def checked(self, tagname):
        tag = self.get_element().find_element_by_xpath(self.toggle_path % tagname)
        return 'x-inactive' not in tag.get_attribute('class')

    def check(self, tagname):
        if not self.checked(tagname):
            self.get_element().find_element_by_xpath(self.toggle_path % tagname).click()

    def uncheck(self, tagname):
        if self.checked(tagname):
            self.get_element().find_element_by_xpath(self.toggle_path % tagname).click()

    @property
    def is_empty(self):
        try:
            with self.driver.implicitly_wait_time(0):
                el = self.get_element().find_element_by_xpath('.//div[@class="x-grid-empty"]')
                return el.is_displayed()
        except NoSuchElementException:
            return False
