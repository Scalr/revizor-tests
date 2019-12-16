from selene.api import s, by
from selene.conditions import visible

from ui.utils import consts
from ui.utils import components
from ui.pages.base import BasePage


class ClassicEnvDashboard(BasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should_not_be(visible)
        s(by.xpath('//div[text()="AWS health status"]')).should_be(visible, timeout=10)
