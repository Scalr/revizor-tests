from selene.api import s, by
from selene.conditions import visible

from .base import TfBasePage


class TerraformEnvDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="Loading page ..." and contains(@class, "x-title-text")]')).should_not_be(visible)
        s(by.xpath('//div[text()="Announcements"]')).should_be(visible, timeout=10)
