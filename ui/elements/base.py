import time
import logging

from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from elements import locators

LOG = logging.getLogger()


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
        LOG.debug('Get element %s text.' % str(self.locator))
        return self.get_element().text

    def get_element(self, show_hidden=False):
        return self.list_elements(show_hidden=show_hidden)[0]

    def list_elements(self, show_hidden=False):
        LOG.debug("Locate element/elements %s" % str(self.locator))
        for _ in range(2):
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
            time.sleep(2)
        raise NoSuchElementException(self.locator[1])

    def mouse_over(self):
        LOG.debug('Mouse over element %s' % str(self.locator))
        self.scroll_into_view()
        element = self.get_element()
        chain = ActionChains(self.driver)
        chain.move_to_element(element)
        chain.perform()

    def visible(self):
        LOG.debug('Check visibily status of the element %s' % str(self.locator))
        elements = self.driver.find_elements(*self.locator)
        if elements:
            return elements[0].is_displayed()
        else:
            LOG.debug('Element %s was not found.' % str(self.locator))
            return False

    def hidden(self):
        return not self.visible()

    def wait_until_condition(self, condition, value=None, timeout=10):
        LOG.debug("Wait until element %s is in condition %s." % (str(self.locator), condition))
        wait = WebDriverWait(self.driver, timeout)
        try:
            if value:
                wait.until(condition(self.locator, value))
            elif condition == EC.staleness_of:
                wait.until(condition(self.get_element()))
            else:
                wait.until(condition(self.locator))
            return True
        except TimeoutException:
            return False

    def scroll_into_view(self):
        LOG.debug('Attempt to scroll element %s into view.' % str(self.locator))
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
        LOG.debug('Click button %s' % str(self.locator))
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
        LOG.debug('Click option %s in split button %s' % (str(self.locator), option))
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
        LOG.debug('Check checkbox %s' % str(self.locator))
        element = self.get_element()
        if 'x-cb-checked' not in element.get_attribute("class"):
            element.click()

    def uncheck(self):
        LOG.debug('Uncheck checkbox %s' % str(self.locator))
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
        LOG.debug('Select option %s in combobox %s' % (option, str(self.locator)))
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
        LOG.debug("Select option %s in menu %s" % (option, str(self.locator)))
        self.get_element().click()
        Button(
            xpath='//* [contains(text(), "%s")]//ancestor::a[starts-with(@id, "menuitem")]' % option,
            driver=self.driver).click()

    def click(self):
        LOG.debug("Click on menu %s" % str(self.locator))
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
        LOG.debug('Select option %s in dropdown %s' % (option, str(self.locator)))
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
        LOG.debug('Write "%s" in input field %s' % (text, str(self.locator)))
        element = self.get_element()
        element.clear()
        element.send_keys(text)


class SearchInput(Input):
    """Input field that filters contents of the page.
       Write method wait for filtration to take effect (waits for 'cancel' button in field to appear).
    """

    def write(self, text):
        LOG.debug('Write text "%s" in search field %s' % (text, str(self.locator)))
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


class TableRow(BaseElement):
    """Any text label inside the table
    """
    _element = None

    def _make_locator(self, label=None, xpath=None):
        if label:
            self.locator = locators.XpathLocator(f"//div [text()='{label}']/ancestor::table[@class='x-grid-item']")
        elif xpath:
            self.locator = locators.XpathLocator(xpath)
        else:
            raise ValueError('No locator policy was provided!')

    def _click_entry_checkbox(self):
        checkbox = self.get_element().find_element_by_xpath("./descendant::div [@class='x-grid-row-checker']")
        if checkbox.is_displayed():
            checkbox.click()

    @property
    def _entry_property(self):
        return self.get_element().get_attribute('class').split()

    def get_element(self, refresh=False):
        if not self._element or refresh:
            self._element = self.driver.find_element(*self.locator)
        return self._element

    def select(self):
        """Only highlight entry: make it active
        """
        self.get_element().click()

    def check(self):
        """Select table entry: make it checkbox is checked
        """
        if 'x-grid-item-selected' not in self._entry_property:
            self._click_entry_checkbox()

    def uncheck(self):
        """Deselect table entry: make it checkbox is unchecked
        """
        if 'x-grid-item-selected' in self._entry_property:
            self._click_entry_checkbox()

    def click_button(self, hint=None, xpath=None):
        """Click table entry button selected by button hint or xpath. Xpath must be relative path.
        """
        button_xpath = xpath or f"./descendant::a [contains(@data-qtip, '{hint}')]"
        button = self.get_element().find_element_by_xpath(button_xpath)
        button.click()

    @property
    def exists(self):
        try:
            if self.get_element(refresh=True):
                return True
        except NoSuchElementException:
            return False


class Filter(BaseElement):
    """Input field marked by text label. Default label Search
    """

    def _make_locator(self, label=None, xpath=None):
        if not xpath:
            label = label or 'Search'
            xpath = f"(//div [text()='{label}'])[last()]/following::input[1]"
        self.locator = locators.XpathLocator(xpath)

    def write(self, text):
        element = self.driver.find_element(self.locator)
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.click(element)
        actions.send_keys(text)
        actions.perform()

