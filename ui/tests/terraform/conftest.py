import urllib.parse
import typing as tp

import pytest
import requests
import _pytest.fixtures

from revizor2.api import IMPL
from revizor2.conf import CONF

from ui.utils import vcs as providers
from ui.utils.datagenerator import generate_name


VCS_PROVIDERS = (
    "GitHub",
    "GitLab",
)


_full_providers_stack = [
    "TestVCSProviders",
]
""" List terraform ui tests used full vcs providers stack  
"""


def pytest_generate_tests(metafunc: _pytest.python.Metafunc) -> None:
    """Setup providers for loggined_vcs fixture
    """
    if metafunc.cls.__name__ in _full_providers_stack:
        arg_values = VCS_PROVIDERS
    else:
        arg_values = (VCS_PROVIDERS[0], )
    metafunc.parametrize("loggined_vcs", arg_values, indirect=True)


@pytest.fixture(scope="session")
def loggined_vcs(
    request: _pytest.fixtures.SubRequest,

) -> tp.Union[providers.VCSGitHub, providers.VCSGitLab]:
    vcs_type = request.param
    credentials = getattr(CONF.credentials, vcs_type.lower())
    provider = getattr(providers, f"VCS{vcs_type}")()
    provider.login(credentials.username, credentials.password)
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
        callback["id"],
        name,
        callback["url"],
        oauth_data["key"],
        oauth_data["secret"],
        loggined_vcs.name.lower(),
    )["auth_url"]
    resp = loggined_vcs.authorize_app(auth_url)
    if "denied" in resp.text:
        raise AssertionError(f"{loggined_vcs.name} is not allowed to oauth: {resp.text}")
    resp = requests.get(resp.headers["Location"], allow_redirects=False)
    if not resp.headers["Location"].startswith("/#/vcs"):
        raise AssertionError(f'Scalr return something wrong: {resp.headers["Location"]}')
    params = urllib.parse.parse_qs(urllib.parse.splitquery(resp.headers["Location"])[1])
    IMPL.vcs.set_auth_token(params["vcsProviderId"], params["code"])
    yield {"name": name, "id": callback["id"]}
    loggined_vcs.delete_oauth(name)
