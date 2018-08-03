import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pypom import Page
from pypom.exception import UsageError

from elements import locators
from elements.base import BaseElement


def wait_for_page_to_load(func, *args, **kwargs):
    """Waits until all 'mask' elements will become hidden and Page loaded == True,
       then returns the page object.
    """
    def wrapper(*args, **kwargs):
        page = func(*args, **kwargs)
        mask = locators.ClassLocator("x-mask")
        for _ in range(10):
            if page.loaded and all(not el.is_displayed() for el in page.driver.find_elements(*mask)):
                return page
            time.sleep(3)
        raise UsageError("Page did not load in 30 seconds.")
    return wrapper


class BasePage(Page):
    """Base class for custom PyPOM Page.
       Sets selenium driver property
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for el in self.__class__.__dict__.values():
            if isinstance(el, BaseElement):
                el.driver = self.driver
