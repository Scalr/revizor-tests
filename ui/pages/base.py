import abc


class BasePage:
    def __new__(cls, *args, **kwargs):
        cls.wait_page_loading()
        return super(BasePage, cls).__new__(cls, *args, **kwargs)

    @staticmethod
    @abc.abstractmethod
    def wait_page_loading():
        pass
