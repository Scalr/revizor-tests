from selenium.webdriver.common.by import By


class XpathLocator(tuple):

    def __new__(cls, value):
        return tuple.__new__(XpathLocator, (By.XPATH, value))


class IdLocator(tuple):

    def __new__(cls, value):
        return tuple.__new__(IdLocator, (By.ID, value))


class NameLocator(tuple):

    def __new__(cls, value):
        return tuple.__new__(NameLocator, (By.NAME, value))


class ClassLocator(tuple):

    def __new__(cls, value):
        return tuple.__new__(ClassLocator, (By.CLASS_NAME, value))


class CSSLocator(tuple):

    def __new__(cls, value):
        return tuple.__new__(CSSLocator, (By.CSS_SELECTOR, value))
