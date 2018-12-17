import re
import time
import base64
import logging
from distutils.version import LooseVersion

import github
import requests
from libcloud.compute.base import NodeImage

from revizor2.api import Server, IMPL
from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.fixtures import tables, resources


LOG = logging.getLogger(__name__)
ORG = 'Scalr'
SCALARIZR_REPO = 'int-scalarizr'
GH = github.GitHub(access_token=CONF.credentials.github.access_token)


def get_clean_image(cloud: Cloud) -> NodeImage:
    if CONF.feature.dist.is_windows or CONF.feature.dist.id == 'coreos':
        table = tables('images-clean')
        search_cond = dict(
            dist=CONF.feature.dist.id,
            platform=CONF.feature.platform.name)
        image_id = list(table.filter(search_cond).first().keys())[0]
        image = list(filter(lambda x: x.id == str(image_id), cloud.list_images()))
        if not image:
            raise AssertionError(f'Image {image_id} not found in cloud {CONF.feature.platform.name}')
        image = image[0]
    else:
        image = cloud.find_image()
    LOG.debug('Obtained clean image %s, Id: %s' % (image.name, image.id))
    return image


# FIXME: lifecycle has func like this, check
def assert_scalarizr_version(server: Server, cloud: Cloud, prev_version: str):
    server.reload()
    command = '/opt/bin/scalarizr -v' if CONF.feature.dist.id == 'coreos' else 'scalarizr -v'
    err_msg = 'Scalarizr version not valid %s:%s'
    node = cloud.get_node(server)
    res = node.run(command).std_out
    LOG.debug('Result from scalarizr -v: %s' % res)
    installed_agent = re.findall('(?:Scalarizr\s)([a-z0-9/./-]+)', res)
    assert installed_agent, "Can't get scalarizr version: %s" % res
    installed_agent = installed_agent[0]
    assert LooseVersion(prev_version) != LooseVersion(installed_agent), \
        err_msg % (prev_version, installed_agent)
    LOG.debug(f'Scalarizr was updated. Pre: {prev_version}, Installed: {installed_agent}')


def start_scalarizr_update_via_ui(server: Server):
    LOG.info('Update scalarizr via Scalr UI')
    IMPL.server.update_scalarizr(server_id=server.id)


def wait_szrupd_status(server: Server, status: str):
    start_time = time.time()
    status = status.strip()
    LOG.info(f'Wait status "{status}" on update process')
    while int(time.time() - start_time) < 900:
        try:
            result = server.upd_api.status(cached=False)
            if result['state'].startswith(status):
                LOG.info('Update process finished with waited status: {}'.format(result['state']))
                return
            elif result['state'].startswith('error') and not status == 'error':
                raise AssertionError('Update process failed with error: {}'.format(result['error']))
            LOG.info(f'Update process on server {server.id} in "{result["state"]}" state, wait status {status}')
            time.sleep(15)
        except AssertionError:
            LOG.error('Update process failed')
            raise
        except BaseException as e:
            LOG.debug('Checking update process raise exception: {}'.format(e))
            server._upd_api = None
            time.sleep(15)
    else:
        raise AssertionError('Until 10 minutes status not: %s, it: %s' % (status, result['state']))


def create_branch_copy(context: dict, branch: str = None, is_patched: bool = False):
    if branch == 'system':
        # Use environ because CONF.feature replace '/' to '-'
        branch = CONF.feature.branch
    elif branch == 'new':
        branch = context['branch_copy_name']
    elif not branch:
        # Use environ because CONF.feature replace '/' to '-'
        branch = CONF.feature.to_branch
    else:
        branch = branch.strip()
    context['branch_copy_name'] = context.get('test_branch_copy', 'test-{}'.format(int(time.time())))
    if is_patched:
        fixture_path = 'scripts/scalarizr_app.py'
        script_path = 'src/scalarizr/app.py'
        content = resources(fixture_path).get()
        commit_msg = 'Patch app.py, corrupt windows start'
    else:
        script_path = 'README.md'
        commit_msg = 'Tested build for {} at {} '.format(branch, time.strftime('%-H:%M:%S'))
        content = 'Scalarizr\n=========\n{}'.format(commit_msg)
    LOG.info('Cloning branch: {} to {}'.format(branch, context['branch_copy_name']))
    git = GH.repos(ORG)(SCALARIZR_REPO).git
    # Get the SHA the current test branch points to
    base_sha = git.refs(f'heads/{branch}').get().object.sha
    # Create a new blob with the content of the file
    blob = git.blobs.post(
        content=base64.b64encode(content.encode()).decode(),
        encoding='base64')
    # Fetch the tree this base SHA belongs to
    base_commit = git.commits(base_sha).get()
    # Create a new tree object with the new blob, based on the old tree
    tree = git.trees.post(
        base_tree=base_commit.tree.sha,
        tree=[{'path': script_path,
               'mode': '100644',
               'type': 'blob',
               'sha': blob.sha}])
    # Create a new commit object using the new tree and point its parent to the current master
    commit = git.commits.post(
        message=commit_msg,
        parents=[base_sha],
        tree=tree.sha)
    base_sha = commit.sha
    LOG.debug(f'Scalarizr service was patched. GitHub api res: {commit}')
    # Finally update the heads/master reference to point to the new commit
    try:
        res = git.refs.post(ref='refs/heads/{}'.format(context['branch_copy_name']), sha=base_sha)
        LOG.debug(f'New branch was created. {res}')
    except github.ApiError:
        res = git.refs('heads/{}'.format(context['branch_copy_name'])).patch(sha=base_sha)
        LOG.debug('New created branch {} was updated.'.format(res.get('ref')))
    context['build_commit_sha'] = base_sha


def waiting_new_package(context: dict):
    '''Get build status'''
    LOG.info('Getting build status for: {}'.format(context['build_commit_sha']))
    label_name = 'continuous-integration/drone/push'
    for _ in range(90):
        res = GH.repos(ORG)(SCALARIZR_REPO).commits(context['build_commit_sha']).status.get()
        if res.statuses:
            status = list(filter(lambda x: x['context'] == label_name, res.statuses))[0]
            LOG.debug(f'Patch commit build status: {status}')
            if status.state == 'success':
                LOG.info(f'Drone status: {status.description}')
                return
            elif status.state == 'failure':
                raise AssertionError(f'Build status is {status.state} . Drone status is failed!')
        time.sleep(60)
    LOG.error('Get build status: Time out of range 90 min!')
    raise Exception(f'Time out of range 90 min! Build status is not success or failure. Drone status == {status.state}')
