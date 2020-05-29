import typing as tp

from selene.api import s, be, query
from revizor2.conf import CONF

from ui.utils import vcs
from ui.utils.components import tooltip
from ui.pages.terraform.vcs import GithubAuthPage, VCSPage
from ui.pages.terraform.dashboard import TerraformEnvDashboard


class VCSMixin:

    dashboard: tp.Optional[TerraformEnvDashboard] = None
    vcs_provider: tp.Optional[tp.Union[vcs.VCSGithub, vcs.VCSGitlab]] = None
    _created_oauth: tp.List = []

    def add_provider(
        self, name: str, secret: tp.Optional[str] = None, wait_message: bool = True
    ) -> VCSPage:
        """
        Go to VCS page from TF dashboard and create provider
        """
        vcs_page = self.dashboard.menu.open_vcs_providers()
        vcs_page.new_vcs_button.click()
        new_form = vcs_page.new_vcs_form
        new_form.vcs_type.set_value("GitHub")
        new_form.name.set(name)
        self.vcs_provider.create_oauth(
            name, new_form.callback_url.get_attribute("value"), "http://my.scalr.com"
        )
        self._created_oauth.append(name)
        settings = self.vcs_provider.get_app_settings(name)
        new_form.client_id.set(settings["key"])
        if secret is None:
            secret = settings["secret"]
        new_form.client_secret.set(secret)
        new_form.client_secret.get(query.value)
        new_form.create_button.click()
        github = GithubAuthPage()
        if not github.authorized:
            github.username.set(CONF.credentials.github.username)
            github.password.set(CONF.credentials.github.password)
            github.submit.click()
        github.authorize_user.click()
        s("div#loading").should(be.not_.existing, timeout=10)
        s("div.x-mask").should(be.not_.visible)
        if wait_message:
            tip = tooltip("Successfully Authorized.")
            tip.element.should(be.visible)
            tip.close()
        return vcs_page
