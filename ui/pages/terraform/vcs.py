import time

from selene.api import s, ss, by, browser
from selene.conditions import visible, exist, clickable, text, url_containing

from .base import TfBasePage, BasePage
from ui.utils.components import button


class ProviderLine:
    def __init__(self, element: browser.element):
        self.element = element

    def toggle(self):
        self.element.s('div.x-grid-row-checker').click()

    @property
    def usage(self):
        return self.element.s('div.x-colored-status').get_attribute('data-qtitle')

    @property
    def name(self):
        return self.element.s('div.x-grid-cell-inner').text.strip()


class NewVCSForm(BasePage):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="New VCS Provider" and contains(@class, "x-component")]')).should_be(visible)

    @property
    def vcs_type(self) -> browser.element:
        return s(by.xpath('//input[@name="type"]'))

    @property
    def name(self) -> browser.element:
        return s(by.xpath('//input[@name="name"]'))

    @property
    def callback_url(self) -> browser.element:
        return s(by.xpath('//input[@name="callbackUrl"]'))

    @property
    def client_id(self) -> browser.element:
        return s(by.xpath('//input[@name="clientId"]'))

    @property
    def client_secret(self) -> browser.element:
        return s(by.xpath('//input[@name="clientSecret"]'))

    @property
    def create_button(self) -> browser.element:
        return button('Create')

    @property
    def cancel_button(self) -> browser.element:
        return button('Cancel')


class EditVCSForm(NewVCSForm):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="Edit VCS Provider" and contains(@class, "x-component")]')).should_be(visible)

    @property
    def reauthorize_button(self) -> browser.element:
        return button('Reauthorize on GitHub')

    @property
    def error(self) -> browser.element:
        return s('div[style*="color: red"] ')


class DeleteConfirmationModal:
    def visible(self):
        return s('div.x-panel-confirm').should_be(visible)

    @property
    def message(self):
        return s('div.x-panel-confirm div.message').text

    @property
    def delete_button(self):
        return ss('div.x-panel-confirm a.x-btn')[0]

    @property
    def cancel_button(self):
        return ss('div.x-panel-confirm a.x-btn')[1]


class VCSPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        time.sleep(1)
        s('div#loading').should_not_be(exist, timeout=20)
        button('New VCS Provider').should_be(clickable)

    @property
    def new_vcs_button(self) -> browser.element:
        return button('New VCS Provider')

    @property
    def delete_button(self) -> browser.element:
        return button(icon='delete')

    @property
    def search(self) -> browser.element:
        return s('li.x-tagfield-input>input')

    @property
    def new_vcs_form(self) -> NewVCSForm:
        return NewVCSForm()

    @property
    def providers(self) -> [ProviderLine]:
        return [ProviderLine(p) for p in ss('tr.x-grid-row')]

    def clean_search_field(self):
        return s('div.x-form-filterfield-trigger-cancel-button').click()


class GithubAuthPage(BasePage):
    authorized = False

    @staticmethod
    def wait_page_loading():
        browser.wait_to(url_containing('github.com'))
        url = browser.driver().current_url
        if 'github.com/login/oauth/authorize' in url:
            GithubAuthPage.authorized = True
            s('p.text-small').should_have(text('Authorizing will redirect to'))
        else:
            s('a[href="https://github.com/contact"]').should_be(visible)

    @property
    def username(self) -> browser.element:
        return s('input[name="login"]')

    @property
    def password(self) -> browser.element:
        return s('input[name="password"]')

    @property
    def submit(self) -> browser.element:
        return s('input[name="commit"]')

    @property
    def authorize_user(self) -> browser.element:
        button = s('button[name="authorize"]')
        button.should_be(clickable)
        return button
