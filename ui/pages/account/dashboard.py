from selene.api import s, by, be

from ui.utils import consts
from ui.utils import components
from ui.pages.base import BasePage


class AccountDashboard(BasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible)
        s(by.xpath('//div[text()="Environments in this account"]')).should(be.visible, timeout=10)
