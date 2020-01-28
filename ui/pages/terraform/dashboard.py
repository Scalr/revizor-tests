from selene.api import s, by, be

from .base import TfBasePage
from ui.utils import consts
from ui.utils import components


class TerraformEnvDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible)
        s(by.xpath('//strong[text()="Getting started"]')).should(be.visible, timeout=10)
