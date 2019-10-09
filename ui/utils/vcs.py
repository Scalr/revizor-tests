import abc

import lxml.html
import requests


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


class VCSGithub(VCSProvider):
    def login(self, login: str, password: str) -> requests.Response:
        tree = lxml.html.fromstring(self._session.get('https://github.com/login').text)
        form = tree.xpath('//form')[0]
        form.fields['login'] = login
        form.fields['password'] = password
        form.fields['webauthn-support'] = 'supported'
        form.fields['webauthn-iuvpaa-support'] = 'unsupported'
        return self._session.post('https://github.com/session', data=dict(form.fields))

    def list_oauth(self):
        tree = lxml.html.fromstring(self._session.get('https://github.com/settings/developers').text)
        apps = tree.xpath('//div[contains(@class, "TableObject-item--primary")]/a')
        return [a.text for a in apps]

    def create_oauth(self, name: str, callback_url: str, homepage: str) -> requests.Response:
        tree = lxml.html.fromstring(self._session.get('https://github.com/settings/applications/new').text)
        form = tree.xpath('//form')[3]
        form.fields['oauth_application[name]'] = name
        form.fields['oauth_application[url]'] = homepage
        form.fields['oauth_application[callback_url]'] = callback_url
        return self._session.post('https://github.com/settings/applications', data=dict(form.fields))

    def delete_oauth(self, name: str):
        tree = lxml.html.fromstring(self._session.get('https://github.com/settings/developers').text)
        app_id = tree.xpath(f'//a[text()="{name}"]')[0].attrib['href'].split('/')[-1]
        app_tree = lxml.html.fromstring(self._session.get(f'https://github.com/settings/applications/{app_id}').text)
        form = app_tree.xpath('//input[@name="_method" and @value="delete"]/parent::form')[0]
        return self._session.post(f'https://github.com{form.action}', data=dict(form.fields))

    def get_app_settings(self, name: str):
        """Return OAuth settings (key, secret)"""
        tree = lxml.html.fromstring(self._session.get('https://github.com/settings/developers').text)
        app_id = tree.xpath(f'//a[text()="{name}"]')[0].attrib['href'].split('/')[-1]
        app_tree = lxml.html.fromstring(self._session.get(f'https://github.com/settings/applications/{app_id}').text)
        keys = app_tree.xpath('//dl[@class="keys"]/dd')
        settings = {
            'key': keys[0].text,
            'secret': keys[1].text
        }
        return settings
