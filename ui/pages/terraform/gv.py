from selene.api import s, be, have

from .base import TfBasePage
from ui.utils import consts
from ui.utils.components import loading_modal


class GVPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible, timeout=20)
        s('[id^=breadcrumbs]').should(have.text('Global Variables'))
