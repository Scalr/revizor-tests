import typing as tp
import time
import logging

from selene.api import s, be

from revizor2.conf import CONF
from ui.pages.terraform import vcs as elements
from ui.pages.terraform.dashboard import TerraformEnvDashboard
from ui.utils import vcs
from ui.utils.components import tooltip


LOG = logging.getLogger(__name__)


class VCSMixin:
    dashboard: tp.Optional[TerraformEnvDashboard] = None
    vcs_provider: tp.Optional[tp.Union[vcs.VCSGitHub, vcs.VCSGitLab]] = None
    _created_oauth: tp.List = []

    def add_provider(
        self, name: str, secret: tp.Optional[str] = None, wait_message: bool = True
    ) -> elements.VCSPage:
        """
        Go to VCS page from TF dashboard and create provider
        """
        credentials = getattr(CONF.credentials, self.vcs_provider.name.lower())
        vcs_page = self.dashboard.menu.open_vcs_providers()
        vcs_page.new_vcs_button.click()
        new_form = vcs_page.new_vcs_form
        new_form.vcs_type.set_value(self.vcs_provider.name)
        new_form.name.set_value(name)
        callback_url = new_form.callback_url.get_attribute("value")
        oauth_attrs = dict(name=name, callback_url=callback_url)
        if self.vcs_provider.name == "GitHub":
            oauth_attrs["homepage"] = "http://my.scalr.com"
        self.vcs_provider.create_oauth(**oauth_attrs)
        self._created_oauth.append(name)
        settings = self.vcs_provider.get_app_settings(name)
        if secret is None:
            secret = settings["secret"]
        LOG.info(f"GitHub secrets: {settings['key']}/{settings['secret']}")
        new_form.client_secret.set_value(secret)
        new_form.client_id.set_value(settings["key"])
        new_form.create_button.click()
        provider_page = getattr(elements, f"{self.vcs_provider.name}AuthPage")()
        if not provider_page.authorized:
            provider_page.username.set(credentials.username)
            provider_page.password.set(credentials.password)
            provider_page.submit.click()
        provider_page.authorize_user.click()
        s("div#loading").should(be.not_.existing, timeout=30)
        s("div.x-mask").should(be.not_.visible)
        if wait_message:
            tip = tooltip("Successfully Authorized.")
            tip.element.should(be.visible)
            tip.close()
        return vcs_page
