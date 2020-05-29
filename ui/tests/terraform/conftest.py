import urllib.parse
import typing as tp

import pytest
import requests
import _pytest.fixtures

from revizor2.api import IMPL
from revizor2.conf import CONF

from ui.utils import vcs
from ui.utils.datagenerator import generate_name


VSC_PROVIDERS = (
    "github",
    "gitlab",
)


@pytest.fixture(scope="session", params=VSC_PROVIDERS)
def loggined_vcs(request: _pytest.fixtures.SubRequest) -> tp.Union[vcs.VCSGithub, vcs.VCSGitlab]:
    provider = getattr(vcs, f"VCS{request.param.capitalize()}")()
    provider.login(CONF.credentials.github.username, CONF.credentials.github.password)
    return provider


@pytest.fixture(scope="session")
def vcs_provider(loggined_vcs, testenv) -> tp.Dict[str, str]:
    name = generate_name()
    callback = IMPL.vcs.get_callback_url()
    oauth_attrs = dict(name=name, callback_url=callback["url"])
    if loggined_vcs.name == "GitHub":
        oauth_attrs["homepage"] = f"https://{testenv.te_id}.test-env.scalr.com"
    loggined_vcs.create_oauth(**oauth_attrs)
    oauth_data = loggined_vcs.get_app_settings(name)
    auth_url = IMPL.vcs.create(
        callback["id"], name, callback["url"], oauth_data["key"], oauth_data["secret"]
    )["auth_url"]
    resp = loggined_vcs.authorize_app(auth_url)
    if "denied" in resp.text:
        raise AssertionError(f"GitHub is not allowed to oauth: {resp.text}")
    resp = requests.get(resp.headers["Location"], allow_redirects=False)
    if not resp.headers["Location"].startswith("/#/vcs"):
        raise AssertionError(f'Scalr return something wrong: {resp.headers["Location"]}')
    params = urllib.parse.parse_qs(urllib.parse.splitquery(resp.headers["Location"])[1])
    IMPL.vcs.set_auth_token(params["vcsProviderId"], params["code"])
    yield {"name": name, "id": callback["id"]}
    loggined_vcs.delete_oauth(name)
