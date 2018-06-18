import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


class XpathLocator(tuple):

    def __new__(self, value):
        return tuple.__new__(XpathLocator, (By.XPATH, value))


class IdLocator(tuple):

    def __new__(self, value):
        return tuple.__new__(IdLocator, (By.ID, value))


class NameLocator(tuple):

    def __new__(self, value):
        return tuple.__new__(NameLocator, (By.NAME, value))


class ClassLocator(tuple):

    def __new__(self, value):
        return tuple.__new__(ClassLocator, (By.CLASS_NAME, value))


class CSSLocator(tuple):

    def __new__(self, value):
        return tuple.__new__(CSSLocator, (By.CSS_SELECTOR, value))


class BaseElement:

    def __init__(self, driver, *args, **kwargs):
        self.driver = driver
        self._make_locator(*args, **kwargs)

    @property
    def text(self):
        return self.get_element().text

    def get_element(self):
        return self.list_elements()[0]

    def list_elements(self):
        for _ in range(5):
            try:
                elements = [el for el in self.driver.find_elements(*self.locator) if el.is_displayed()]
                if elements:
                    return elements
            except StaleElementReferenceException:
                continue
            time.sleep(6)
        raise NoSuchElementException(self.locator[1])

    def displayed(self, timeout=3):
        start = time.time()
        while (time.time() - start) < timeout:
            elements = self.driver.find_elements(*self.locator)
            if elements and elements[0].is_displayed():
                return True
            time.sleep(3)
        return False


class Button(BaseElement):

    def _make_locator(self, name=None, text=None, href=None, icon=None, xpath=None):
        if name:
            self.locator = NameLocator(name)
        elif text:
            self.locator = XpathLocator('//* [contains(text(), "%s")]//ancestor::a' % text)
        elif href:
            self.locator = XpathLocator('//a [@href="%s"]' % href)
        elif icon:
            self.locator = XpathLocator('//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def click(self):
        self.get_element().click()


class SplitButton(BaseElement):

    def _make_locator(self, xpath=None):
        if xpath:
            self.locator = XpathLocator(xpath)
        else:
            self.locator = XpathLocator('//a [starts-with(@id, "splitbutton")]')

    def click(self, option):
        main_button = self.get_element()
        chain = ActionChains(self.driver.driver)
        chain.move_to_element(main_button)
        chain.move_by_offset(50, 0)
        chain.click()
        chain.perform()
        Button(self.driver, text=option).click()


class Checkbox(BaseElement):

    def _make_locator(self, value=None, xpath=None):
        if value:
            self.locator = XpathLocator('//* [@data-value="%s"]' % value.lower())
        elif xpath:
            self.locator = XpathLocator(xpath)
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

    def _make_locator(self, text=None, xpath=None, span=True):
        self.span = span
        if text:
            self.locator = XpathLocator(
                '//span[contains(text(), "%s")]//ancestor::div[starts-with(@id, "combobox")]' % text)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        if self.span:
            Button(self.driver, xpath='//span[contains(text(), "%s")]//parent::li' % option).click()
        else:
            Button(self.driver, xpath='//li[contains(text(), "%s")]' % option).click()


class Menu(BaseElement):

    def _make_locator(self, label=None, xpath=None):
        if label:
            self.locator = XpathLocator('//* [contains(text(), "%s")]//preceding-sibling::a' % label)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        Button(
            self.driver,
            xpath='//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option).click()


class Dropdown(BaseElement):

    def _make_locator(self, input_name=None, xpath=None):
        if input_name:
            self.locator = XpathLocator('//input [@name="%s"]' % input_name)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option):
        self.get_element().click()
        Button(self.driver, xpath='//* [contains(text(), "%s")]//parent::div' % option).click()


class Input(BaseElement):

    def _make_locator(self, name=None, label=None, xpath=None):
        if name:
            self.locator = XpathLocator('//input [contains(@name, "%s")]' % name)
        elif label:
            self.locator = XpathLocator('//* [contains(text(),"%s")]//following::input' % label)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def write(self, text):
        element = self.get_element()
        element.clear()
        element.send_keys(text)


class Label(BaseElement):

    def _make_locator(self, text=None, xpath=None):
        if text:
            self.locator = XpathLocator('//* [contains(text(), "%s")]' % text)
        elif xpath:
            self.locator = XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')
