from selene.api import ss, by, be, have

from .base import TfBasePage
from ui.utils import consts
from ui.utils import components


class TerraformEnvDashboard(TfBasePage):
    @staticmethod
    def wait_page_loading():
        components.loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible)
        ss(by.xpath('//*[normalize-space(text())="Getting started"]')).filtered_by(be.visible).should(have.size(1))
