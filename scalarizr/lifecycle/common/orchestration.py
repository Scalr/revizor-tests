import logging
import typing as tp

import chef

from revizor2.api import Server
from scalarizr.lib import server as lib_server

LOG = logging.getLogger(__name__)


def assert_recipes_in_runlist(server: Server, recipes: tp.List[str]):
    host_name = lib_server.get_hostname_by_server_format(server)
    chef_api = chef.autoconfigure()

    run_list = chef.Node(host_name, api=chef_api).run_list
    if len(run_list) != len(recipes):
        raise AssertionError('Number of recipes in the node is wrong: "%s" != "%s". Actual runlist in Chef Node: "%s"' %
                             (len(run_list), len(recipes), run_list))
    if not all(recipe in ','.join(run_list) for recipe in recipes):
        raise AssertionError('Recipe "%s" is not in the runlist!' % run_list)
