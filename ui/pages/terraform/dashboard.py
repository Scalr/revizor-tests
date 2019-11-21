from selene.api import s, by
from selene.conditions import visible

from .base import TfBasePage
from ui.utils import consts
from ui.utils import components


class TerraformEnvDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should_not_be(visible)
        s(by.xpath('//div[text()="Announcements"]')).should_be(visible, timeout=10)
