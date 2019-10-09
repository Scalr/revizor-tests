import typing as tp

import pytest
import _pytest.fixtures

from revizor2.conf import CONF

from ui.utils import vcs


@pytest.fixture(scope="module", params=['github'])
def vcs_provider(request: _pytest.fixtures.SubRequest) -> tp.Union[vcs.VCSGithub]:
    provider = getattr(vcs, f'VCS{request.param.capitalize()}')()
    provider.login(CONF.credentials.github.username, CONF.credentials.github.password)
    return provider
