from selene.api import s, ss, be, have

from .base import TfBasePage
from ui.utils import consts
from ui.utils.components import loading_modal


class EndpointsPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible, timeout=20)
        s('div.x-mask-loading').should(be.not_.visible, timeout=10)
        s('[id^=breadcrumbs]').should(have.text('Endpoints'))


class WebhooksPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        loading_modal(consts.LoadingModalMessages.LOADING_PAGE).should(be.not_.visible, timeout=20)
        ss('div.x-grid-buffered-loader').should(be.not_.visible, timeout=10)
        s('[id^=breadcrumbs]').should(have.text('Webhooks'))

