import abc
import logging

import lxml.html
import requests
import urllib
import typing as tp

LOG = logging.getLogger(__name__)


class VCSProvider(metaclass=abc.ABCMeta):
    name: str = None

    def __init__(self):
        self._session = requests.Session()

    @abc.abstractmethod
    def login(self, login: str, password: str):
        raise NotImplementedError

    @abc.abstractmethod
    def create_oauth(self, name: str, callback_url: str, homepage: str):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_oauth(self, name: str):
        raise NotImplementedError


class VCSGitLab(VCSProvider):

    name = "GitLab"
    _uri = "https://gitlab.com"

    def _get_url(self, path: str) -> str:
        return urllib.parse.urljoin(self._uri, path)

    def _get_app_elements_tree(self, path: tp.Optional[str] = None) -> lxml.html.HtmlElement:
        path = path or "/profile/applications"
        return lxml.html.fromstring(self._session.get(self._get_url(path)).text)

    def login(self, login: str, password: str) -> requests.Response:
        path = "/users/sign_in"
        url = self._get_url(path)
        tree = lxml.html.fromstring(self._session.get(url).text)
        form = list(filter(lambda f: f.action == path, tree.forms))[0]
        form.fields["user[login]"] = login
        form.fields["user[password]"] = password
        form.fields["user[remember_me]"] = b"0"
        return self._session.post(url, data=dict(form.fields))

    def list_oauth(self) -> tp.Union[tp.List[str,], tp.List]:
        tree = self._get_app_elements_tree()
        apps = tree.xpath('//table//tr[contains(@id, "application")]/td[1]/a')
        return [app.text for app in apps]

    def create_oauth(self, name: str, callback_url: str) -> requests.Response:
        tree = self._get_app_elements_tree()
        form = tree.get_element_by_id("new_doorkeeper_application")
        form.fields["doorkeeper_application[name]"] = name
        form.fields["doorkeeper_application[redirect_uri]"] = callback_url
        form.fields["doorkeeper_application[confidential]"] = b"1"
        path = "/oauth/applications"
        return self._session.post(self._get_url(path), data=dict(form.fields))

    def delete_oauth(self, name: str) -> requests.Response:
        tree = self._get_app_elements_tree()
        path = tree.xpath(f'//a[text()="{name}"]')[0].attrib["href"]
        form = tree.xpath(f'//form[@action="{path}"]')[0]
        form.fields["_method"] = "delete"
        return self._session.post(self._get_url(path), data=(dict(form.fields)))

    def get_app_settings(self, name: str) -> tp.Dict[str, str]:
        """Return OAuth settings (key, secret)"""
        tree = self._get_app_elements_tree()
        path = tree.xpath(f'//a[text()="{name}"]')[0].attrib["href"]
        tree = self._get_app_elements_tree(path)
        return dict(
            key=tree.xpath('//input[@id="application_id"]')[0].value,
            secret=tree.xpath('//input[@id="secret"]')[0].value,
        )

    def authorize_app(self, url: str) -> requests.Response:
        tree = lxml.html.fromstring(self._session.get(url).text)
        form = tree.xpath('//*[@value="Authorize"]/parent::form')[0]
        fields = dict(form.fields)
        return self._session.post(self._get_url(form.action), data=fields, allow_redirects=False)


class VCSGitHub(VCSProvider):

    name = "GitHub"

    def login(self, login: str, password: str) -> requests.Response:
        tree = lxml.html.fromstring(self._session.get("https://github.com/login").text)
        form = list(filter(lambda f: f.action == "/session", tree.forms))[0]
        form.fields["login"] = login
        form.fields["password"] = password
        form.fields["webauthn-support"] = "supported"
        form.fields["webauthn-iuvpaa-support"] = "unsupported"
        return self._session.post("https://github.com/session", data=dict(form.fields))

    def list_oauth(self):
        tree = lxml.html.fromstring(
            self._session.get("https://github.com/settings/developers").text
        )
        apps = tree.xpath('//div[contains(@class, "TableObject-item--primary")]/a')
        return [a.text for a in apps]

    def create_oauth(self, name: str, callback_url: str, homepage: str) -> requests.Response:
        tree = lxml.html.fromstring(
            self._session.get("https://github.com/settings/applications/new").text
        )
        form = tree.xpath("//form[@id='new_oauth_application']")[0]
        form.fields["oauth_application[name]"] = name
        form.fields["oauth_application[url]"] = homepage
        form.fields["oauth_application[callback_url]"] = callback_url
        return self._session.post(
            "https://github.com/settings/applications", data=dict(form.fields)
        )

    def delete_oauth(self, name: str):
        tree = lxml.html.fromstring(
            self._session.get("https://github.com/settings/developers").text
        )
        app_id = tree.xpath(f'//a[text()="{name}"]')[0].attrib["href"].split("/")[-1]
        app_tree = lxml.html.fromstring(
            self._session.get(f"https://github.com/settings/applications/{app_id}/advanced").text
        )
        form = app_tree.xpath('//input[@name="_method" and @value="delete"]/parent::form')[0]
        return self._session.post(f"https://github.com{form.action}", data=dict(form.fields))

    def authorize_app(self, url: str):
        tree = lxml.html.fromstring(self._session.get(url).text)
        form = tree.forms[0]
        fields = dict(form.fields)
        fields["authorize"] = 1
        return self._session.post(
            f"https://github.com{form.action}", data=fields, allow_redirects=False
        )

    def get_app_settings(self, name: str):
        """Return OAuth settings (key, secret)"""
        tree = lxml.html.fromstring(
            self._session.get("https://github.com/settings/developers").text
        )
        app_id = tree.xpath(f'//a[text()="{name}"]')[0].attrib["href"].split("/")[-1]
        app_tree = lxml.html.fromstring(
            self._session.get(f"https://github.com/settings/applications/{app_id}").text
        )
        keys = app_tree.xpath('//dl[@class="keys"]/dd')
        settings = {"key": keys[0].text, "secret": keys[1].text}
        return settings
