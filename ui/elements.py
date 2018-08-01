import time

from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import locators


class BaseElement:
    """Base class for UI element types.
    """
    locator = None

    def __init__(self, *args, **kwargs):
        self.driver = kwargs.pop('driver') if 'driver' in kwargs else None
        self._make_locator(*args, **kwargs)

    def _make_locator(self, *args, **kwargs):
        raise NotImplementedError("BaseElement should not be used directly.")

    @property
    def text(self):
        return self.get_element().text

    def get_element(self, show_hidden=False):
        return self.list_elements(show_hidden=show_hidden)[0]

    def list_elements(self, show_hidden=False):
        for _ in range(5):
            try:
                if show_hidden:
                    elements = self.driver.find_elements(*self.locator)
                else:
                    elements = [el for el in self.driver.find_elements(*self.locator) if el.is_displayed()]
                if elements:
                    return elements
            except StaleElementReferenceException:
                continue
            time.sleep(6)
        raise NoSuchElementException(self.locator[1])

    def mouse_over(self):
        self.scroll_into_view()
        element = self.get_element()
        chain = ActionChains(self.driver)
        chain.move_to_element(element)
        chain.perform()

    def visible(self, timeout=3):
        start = time.time()
        while (time.time() - start) < timeout:
            elements = self.driver.find_elements(*self.locator)
            if elements and elements[0].is_displayed():
                return True
            time.sleep(3)
        return False

    def hidden(self, timeout=3):
        return not self.visible(timeout=timeout)

    def scroll_into_view(self):
        if self.hidden():
            self.driver.execute_script(
                "arguments[0].scrollIntoView();", self.driver.find_elements(*self.locator)[0])


class Button(BaseElement):

    def _make_locator(self, element_id=None, name=None, text=None, href=None, icon=None, class_name=None, xpath=None):
        if element_id:
            self.locator = locators.IdLocator(element_id)
        elif name:
            self.locator = locators.NameLocator(name)
        elif text:
            self.locator = locators.XpathLocator('//* [contains(text(), "%s")]//ancestor::a' % text)
        elif href:
            self.locator = locators.XpathLocator('//a [@href="%s"]' % href)
        elif icon:
            self.locator = locators.XpathLocator('//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        elif class_name:
            self.locator = locators.ClassLocator(class_name)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def click(self):
        self.get_element().click()


class SplitButton(BaseElement):
    """Button with dropdown that has different options.
       Example - Save Farm/Save & Launch in Farm Designer page.
    """

    def _make_locator(self, xpath=None):
        if xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            self.locator = locators.XpathLocator('//a [starts-with(@id, "splitbutton")]')

    def click(self, option):
        """Clicks on desired option in split button.

           :param str option: text in option element.
        """
        main_button = self.get_element()
        chain = ActionChains(self.driver)
        chain.move_to_element(main_button)
        chain.move_by_offset(50, 0)
        chain.click()
        chain.perform()
        Button(text=option, driver=self.driver).click()


class Checkbox(BaseElement):

    def _make_locator(self, value=None, text=None, xpath=None):
        if value:
            self.locator = locators.XpathLocator('//* [@data-value="%s"]' % value.lower())
        elif text:
            self.locator = locators.XpathLocator(
                '//* [contains(text(), "%s")]//preceding-sibling::input [@role="checkbox"]' % text)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def check(self):
        element = self.get_element()
        if 'x-cb-checked' not in element.get_attribute("class"):
            element.click()

    def uncheck(self):
        element = self.get_element()
        if 'x-cb-checked' in element.get_attribute("class"):
            element.click()


class Combobox(BaseElement):
    """Dropdown with multiple selectable options.
    """

    def _make_locator(self, text=None, xpath=None, span=True):
        """
           :param bool span: identifies whether text is in child //span element
        """
        self.span = span
        if text:
            self.locator = locators.XpathLocator(
                '//span[contains(text(), "%s")]//ancestor::div[starts-with(@id, "combobox")]' % text)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        if self.span:
            Button(xpath='//span[contains(text(), "%s")]//parent::li' % option, driver=self.driver).click()
        else:
            Button(xpath='//li[contains(text(), "%s")]' % option, driver=self.driver).click()


class Menu(BaseElement):
    """Menu with clickable Buttons (typically 'menuitem' in element's id).
    """

    def _make_locator(self, label=None, icon=None, xpath=None):
        if label:
            self.locator = locators.XpathLocator('//* [contains(text(), "%s")]//preceding-sibling::a' % label)
        elif icon:
            self.locator = locators.XpathLocator(
                '//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        Button(
            xpath='//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option,
            driver=self.driver).click()

    def click(self):
        self.get_element().click()


class Dropdown(BaseElement):

    def _make_locator(self, input_name=None, xpath=None):
        """
           :param str input_name: @name of the //input field
        """
        if input_name:
            self.locator = locators.XpathLocator('//input [@name="%s"]' % input_name)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        Button(xpath='//* [contains(text(), "%s")]//parent::div' % option, driver=self.driver).click()


class Input(BaseElement):
    """Any writable field element, typically search and filter field
    """

    def _make_locator(self, name=None, label=None, xpath=None):
        if name:
            self.locator = locators.XpathLocator('//input [contains(@name, "%s")]' % name)
        elif label:
            self.locator = locators.XpathLocator('//* [contains(text(),"%s")]//following::input' % label)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def write(self, text):
        element = self.get_element()
        element.clear()
        Button(xpath='//div [contains(@id, "trigger-cancelButton")]', driver=self.driver).hidden()
        element.send_keys(text)
        Button(xpath='//div [contains(@id, "trigger-cancelButton")]', driver=self.driver).visible()


class Label(BaseElement):
    """Any non-clickable element with text
    """

    def _make_locator(self, text=None, xpath=None):
        if text:
            self.locator = locators.XpathLocator('//* [contains(text(), "%s")]' % text)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')


class ScalrMainMenu:

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
            raise ValueError("Scrolling direction must be 'down' or 'up', not %s!" % direction)
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
