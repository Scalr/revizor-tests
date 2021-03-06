import time
from selene.api import s, ss, by, browser, be, have, query

from .base import TfBasePage, BasePage
from ui.utils import components


class ProviderLine:
    def __init__(self, element: browser.element):
        self.element = element

    def toggle(self):
        self.element.s("div.x-grid-checkcolumn-cell-inner").click()

    @property
    def usage(self):
        return self.element.s("div.x-colored-status").get_attribute("data-qtitle")

    @property
    def name(self):
        return self.element.s("div.x-grid-cell-inner").text.strip()


class NewVCSForm(BasePage):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="New VCS Provider" and contains(@class, "x-component")]')).should(
            be.visible
        )

    @property
    def vcs_type(self) -> components.combobox:
        return components.combobox("Type")

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
        return components.button("Create")

    @property
    def cancel_button(self) -> browser.element:
        return components.button("Cancel")


class EditVCSForm(NewVCSForm):
    @staticmethod
    def wait_page_loading():
        s(by.xpath('//div[text()="Edit VCS Provider" and contains(@class, "x-component")]')).should(
            be.visible
        )

    @property
    def reauthorize_button(self) -> browser.element:
        return components.button(xpath=f'//span[contains(text(), "Reauthorize on")]//ancestor::a')

    @property
    def error(self) -> browser.element:
        return s('div[style*="color: red"] ')


class DeleteConfirmationModal:
    def visible(self):
        return s("div.x-panel-confirm").should(be.visible)

    @property
    def message(self):
        return s("div.x-panel-confirm div.message").get(query.text)

    @property
    def delete_button(self):
        return ss("div.x-panel-confirm a.x-btn")[0]

    @property
    def cancel_button(self):
        return ss("div.x-panel-confirm a.x-btn")[1]


class VCSPage(TfBasePage):
    @staticmethod
    def wait_page_loading():
        s("div#loading").should(be.not_.existing, timeout=20)
        ss("div.x-grid-buffered-loader").should(be.not_.visible, timeout=10)
        components.button("New VCS Provider").should(be.visible).should(
            have.no.css_class("x-item-disabled")
        ).should(have.no.css_class("x-btn-disabled"))

    @property
    def new_vcs_button(self) -> components.button:
        return components.button("New VCS Provider")

    @property
    def delete_button(self) -> components.button:
        return components.button(icon="delete")

    @property
    def search(self) -> browser.element:
        return s("li.x-tagfield-input>input")

    @property
    def new_vcs_form(self) -> NewVCSForm:
        return NewVCSForm()

    @property
    def providers(self) -> [ProviderLine]:
        return [ProviderLine(p) for p in ss("tr.x-grid-row")]

    def clean_search_field(self):
        return s("div.x-form-filterfield-trigger-cancel-button").click()


class GitHubAuthPage(BasePage):
    authorized = False

    @staticmethod
    def wait_page_loading():
        browser.wait_to(have.url_containing("github.com"))
        url = browser.driver().current_url
        if "github.com/login/oauth/authorize" in url:
            GitHubAuthPage.authorized = True
            s("p.text-small").should(have.text("Authorizing will redirect to"))
        else:
            s('a[href="https://github.com/contact"]').should(be.visible)

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
        button = s(by.xpath('//button[starts-with(text(), "Authorize")]')).should(be.clickable)
        return button


class GitLabAuthPage(BasePage):

    authorized = False

    @staticmethod
    def wait_page_loading() -> None:
        browser.wait_to(have.url_containing("gitlab.com"))
        url = browser.driver().current_url
        if "gitlab.com/oauth/authorize" in url:
            GitLabAuthPage.authorized = True
            s('input[value="Authorize"]').should(be.visible)
        else:
            s('a[href="https://about.gitlab.com/"]').should(be.visible)

    @property
    def username(self) -> browser.element:
        return s('input[name="user[login]"]')

    @property
    def password(self) -> browser.element:
        return s('input[name="user[password]"]')

    @property
    def submit(self) -> browser.element:
        return s('input[name="commit"]')

    @property
    def authorize_user(self) -> browser.element:
        button = s('input[value="Authorize"]')
        button.with_(timeout=5).should(be.visible).should(be.clickable)
        return button
