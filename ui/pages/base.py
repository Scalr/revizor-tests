import time
import logging

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pypom import Page
from pypom.exception import UsageError

from elements import locators
from elements.base import BaseElement, Label, Button

LOG = logging.getLogger()


class invisibility_of_all_elements_located(object):
    """Custom Selenium Expected Condition.
       Check the all elements with specified locator are invisible
    """

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        elements = driver.find_elements(*self.locator)
        for element in elements:
            try:
                if element.is_displayed():
                    return False
            except StaleElementReferenceException:
                continue
        return True


def wait_for_page_to_load(func, *args, **kwargs):
    """Waits until all 'mask' elements will become hidden and Page loaded == True,
       then returns the page object.
    """
    def wrapper(*args, **kwargs):
        timeout = kwargs.pop('timeout', 30)
        page = func(*args, **kwargs)
        mask = locators.ClassLocator("x-mask")
        wait = WebDriverWait(page.driver, timeout=timeout)
        LOG.debug("Waiting for loading element with class='x-mask' to drop")
        try:
            wait.until(invisibility_of_all_elements_located(mask))
            time.sleep(1)
            if page.loaded:
                return page
        except TimeoutException:
            pass
        raise UsageError(f"Page did not load in {timeout} seconds.")
    return wrapper


class BasePage(Page):
    """Base class for custom PyPOM Page.
       Sets selenium driver property
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def apply_driver(element):
            if isinstance(element, BaseElement):
                element.driver = self.driver

        for cls in self.__class__.mro():
            if issubclass(cls, BasePage):
                for el in cls.__dict__.values():
                    apply_driver(el)

    @property
    def page_message(self):
        return Label(
            xpath='//div[starts-with(@id, "tooltip") and contains(@class, "x-tip-message")]',
            driver=self.driver)
