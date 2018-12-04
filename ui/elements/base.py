import time

from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from elements import locators


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
                    elements = [el for el in self.driver.find_elements(
                        *self.locator) if el.is_displayed()]
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

    def visible(self):
        elements = self.driver.find_elements(*self.locator)
        if elements:
            return elements[0].is_displayed()
        else:
            return False

    def hidden(self):
        return not self.visible()

    def wait_until_condition(self, condition, value=None, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            if value:
                wait.until(condition(self.locator, value))
            else:
                wait.until(condition(self.locator))
            return True
        except TimeoutException:
            return False

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
            self.locator = locators.XpathLocator(
                '//* [contains(text(), "%s")]//ancestor::a' % text)
        elif href:
            self.locator = locators.XpathLocator('//a [@href="%s"]' % href)
        elif icon:
            self.locator = locators.XpathLocator(
                '//* [contains(@class, "x-btn-icon-%s")]//ancestor::a' % icon)
        elif class_name:
            self.locator = locators.ClassLocator(class_name)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def click(self):
        # self.wait_until_condition(EC.element_to_be_clickable, timeout=3)
        self.get_element().click()


class SplitButton(BaseElement):
    """Button with dropdown that has different options.
       Example - Save Farm/Save & Launch in Farm Designer page.
    """

    def _make_locator(self, xpath=None):
        if xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            self.locator = locators.XpathLocator(
                '//a [starts-with(@id, "splitbutton")]')

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
            self.locator = locators.XpathLocator(
                '//* [@data-value="%s"]' % value.lower())
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
            Button(xpath='//span[contains(text(), "%s")]//parent::li' %
                   option, driver=self.driver).click()
        else:
            Button(xpath='//li[contains(text(), "%s")]' %
                   option, driver=self.driver).click()


class Menu(BaseElement):
    """Menu with clickable Buttons (typically 'menuitem' in element's id).
    """

    def _make_locator(self, label=None, icon=None, xpath=None):
        if label:
            self.locator = locators.XpathLocator(
                '//* [contains(text(), "%s")]//preceding-sibling::a' % label)
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
            self.locator = locators.XpathLocator(
                '//input [@name="%s"]' % input_name)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def select(self, option, hide_options=False):
        xpath = "(//* [text()='{}'])[position()=1]".format(option)
        self.get_element().click()
        Button(xpath=xpath, driver=self.driver).click()
        if hide_options:
            xpath = "//".join((xpath, "following::div [contains(@class, 'x-form-arrow-trigger')][position()=1]"))
            Button(xpath=xpath, driver=self.driver).click()


class Input(BaseElement):
    """Any writable field element.
    """

    def _make_locator(self, name=None, label=None, xpath=None):
        if name:
            self.locator = locators.XpathLocator(
                '//input [contains(@name, "%s")]' % name)
        elif label:
            self.locator = locators.XpathLocator(
                '//* [contains(text(),"%s")]//following::input' % label)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def write(self, text):
        element = self.get_element()
        element.clear()
        element.send_keys(text)


class SearchInput(Input):
    """Input field that filters contents of the page.
       Write method wait for filtration to take effect (waits for 'cancel' button in field to appear).
    """

    def write(self, text):
        element = self.get_element()
        element.clear()
        Button(xpath='//div [contains(@id, "trigger-cancelButton")]',
               driver=self.driver).wait_until_condition(EC.invisibility_of_element_located, timeout=3)
        element.send_keys(text)
        Button(xpath='//div [contains(@id, "trigger-cancelButton")]',
               driver=self.driver).wait_until_condition(EC.visibility_of_element_located, timeout=3)


class Label(BaseElement):
    """Any non-clickable element with text
    """

    def _make_locator(self, text=None, xpath=None):
        if text:
            self.locator = locators.XpathLocator(
                '//* [contains(text(), "%s")]' % text)
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')
