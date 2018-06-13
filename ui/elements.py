import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


class BaseElement():

    def __init__(self, driver):
        self.driver = driver
        self.locator = None

    @property
    def text(self, custom_locator=None):
        return self.get_element(custom_locator=custom_locator).text

    def get_element(self, custom_locator=None):
        return self.list_elements(custom_locator=custom_locator)[0]

    def list_elements(self, custom_locator=None):
        locator = custom_locator or self.locator
        for _ in range(5):
            try:
                elements = [el for el in self.driver.find_elements(*locator) if el.is_displayed()]
                if elements:
                    return elements
            except StaleElementReferenceException:
                continue
            time.sleep(6)
        raise NoSuchElementException(locator[1])

    def displayed(self, timeout=3):
        start = time.time()
        while (time.time() - start) < timeout:
            elements = self.driver.find_elements(*self.locator)
            if elements and elements[0].is_displayed():
                return True
            time.sleep(3)
        return False


class Button(BaseElement):

    def __init__(self, driver, name=None, text=None, href=None, icon=None, xpath=None):
        super().__init__(driver)
        if name:
            self.locator = (By.NAME, name)
        elif text:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]//ancestor::a' % text)
        elif href:
            self.locator = (By.XPATH, '//a [@href="%s"]' % href)
        elif icon:
            self.locator = (By.XPATH, '//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        else:
            self.locator = (By.XPATH, xpath)

    def click(self):
        self.get_element().click()


class SplitButton(BaseElement):

    def __init__(self, driver, xpath=None):
        super().__init__(driver)
        if xpath:
            self.locator = (By.XPATH, xpath)
        else:
            self.locator = (By.XPATH, '//a [starts-with(@id, "splitbutton")]')

    def click(self, option):
        main_button = self.get_element()
        chain = ActionChains(self.driver.driver)
        chain.move_to_element(main_button)
        chain.move_by_offset(50, 0)
        chain.click()
        chain.perform()
        Button(self.driver, text=option).click()


class Checkbox(BaseElement):

    def __init__(self, driver, value=None, xpath=None):
        super().__init__(driver)
        if value:
            self.locator = (By.XPATH, '//* [@data-value="%s"]' % value.lower())
        else:
            self.locator = (By.XPATH, xpath)

    def check(self):
        element = self.get_element()
        if 'x-cb-checked' not in element.get_attribute("class"):
            element.click()

    def uncheck(self):
        element = self.get_element()
        if 'x-cb-checked' in element.get_attribute("class"):
            element.click()


class Combobox(BaseElement):

    def __init__(self, driver, text=None, xpath=None, span=True):
        super().__init__(driver)
        self.span = span
        if text:
            self.locator = (
                By.XPATH,
                '//span[contains(text(), "%s")]//ancestor::div[starts-with(@id, "combobox")]' % text)
        else:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element().click()
        if self.span:
            option_locator = (By.XPATH, '//span[contains(text(), "%s")]//parent::li' % option)
        else:
            option_locator = (By.XPATH, '//li[contains(text(), "%s")]' % option)
        self.get_element(custom_locator=option_locator).click()


class Menu(BaseElement):

    def __init__(self, driver, label=None, xpath=None):
        super().__init__(driver)
        if label:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]//preceding-sibling::a' % label)
        elif xpath:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element().click()
        option_locator = (By.XPATH, '//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option)
        self.get_element(custom_locator=option_locator).click()


class Dropdown(BaseElement):

    def __init__(self, driver, input_name=None, xpath=None):
        super().__init__(driver)
        if input_name:
            self.locator = (By.XPATH, '//input [@name="%s"]' % input_name)
        else:
            self.locator = (By.XPATH, xpath)

    def select(self, option):
        self.get_element().click()
        option_locator = (By.XPATH, '//* [contains(text(), "%s")]//parent::div' % option)
        self.get_element(custom_locator=option_locator).click()


class Input(BaseElement):

    def __init__(self, driver, name=None, label=None, xpath=None):
        super().__init__(driver)
        if name:
            self.locator = (By.XPATH, '//input [contains(@name, "%s")]' % name)
        elif label:
            self.locator = (By.XPATH, '//* [contains(text(),"%s")]//following::input' % label)
        else:
            self.locator = (By.XPATH, xpath)

    def write(self, text):
        element = self.get_element()
        element.clear()
        element.send_keys(text)


class Label(BaseElement):

    def __init__(self, driver, text=None, xpath=None):
        super().__init__(driver)
        if text:
            self.locator = (By.XPATH, '//* [contains(text(), "%s")]' % text)
        else:
            self.locator = (By.XPATH, xpath)
