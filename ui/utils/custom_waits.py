# coding: utf-8
"""
Created on 06.02.19
@author: Eugeny Kurkovich
"""

from selenium.webdriver.remote.webelement import WebElement


class element_class_value_no_presence_of(object):
    """An expectation for checking that an element class has no some value.

    obj - locator or WebElement class instance
    returns the WebElement once it no has some class value
    """
    def __init__(self, obj, class_value):
        self.obj = obj
        self.class_value = class_value

    def __call__(self, driver):
        # Finding the referenced element
        if not isinstance(self.obj, WebElement):
            element = driver.find_element(*self.obj)
        else:
            element = self.obj
        if self.class_value not in element.get_attribute("class").split():
            return element
        return False

