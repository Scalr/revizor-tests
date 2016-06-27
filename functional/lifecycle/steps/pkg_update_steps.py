# coding: utf-8

"""
Created on 09.01.2015
@author: Eugeny Kurkovich
"""
import os
import re
import time
import base64
import github
import logging
try:
    import winrm
except ImportError:
    raise ImportError("Please install WinRM")

from datetime import datetime
from revizor2.api import IMPL, Platform
from revizor2.conf import CONF
from collections import namedtuple
from lettuce import step, world, after
from urllib2 import URLError

from revizor2.consts import Dist
from revizor2.defaults import USE_VPC
from distutils.version import LooseVersion
from revizor2.utils import wait_until
from revizor2.fixtures import tables, resources

LOG = logging.getLogger(__name__)

ORG = 'Scalr'
SCALARIZR_REPO = 'int-scalarizr'
GH = github.GitHub(access_token=CONF.main.github_access_token)


@step(r"I have manually installed scalarizr(?:\s('[\w\W\d]+'))* on ([\w\d]+)")
def havinng_installed_scalarizr(step, version=None, serv_as=None):
    version = (version or '').replace("'", '')
    setattr(world, serv_as, None)
    if version:
        setattr(world, 'default_agent', version.strip())
    step.behave_as("""
        Given I have a clean image
        And I add image to the new role
        When I have a an empty running farm
        Then I add created role to the farm
        And I see pending server {serv_as}
        When I install scalarizr {version} to the server {serv_as}{manually}
        Then I forbid {pkg_type}scalarizr update at startup and run it on {serv_as}
        And I wait and see running server {serv_as}""".format(
            version=version,
            serv_as=serv_as,
            pkg_type='legacy ' if version.strip() == '3.8.5' else 'msi ',
            manually='' if version else ' manually'))


@step(r"I build (new|corrupt) package")
def having_new_package(step, pkg_type):
    if pkg_type == 'new':
        patched = ''
    else:
        patched = ' with patched script'
    step.behave_as("""
        Given I have a copy of the branch{patched}
        Then I wait for new package was built
    """.format(patched=patched))


@step(r"I set branch with (?:corrupt|new) package for role")
def setting_new_devel_branch(step):
   step.given("I change branch to {} for role".format(world.test_branch_copy))


@step(r"I install (?:corrupt|new) package to the server ([\w\d]+)")
def installing_new_package(step, serv_as):
    branch = getattr(world, 'test_branch_copy')
    step.given("I install new scalarizr to the server {} from the branch {}".format(serv_as, branch.strip()))


@step('I have a copy of the(?: (.+))? branch( with patched script)?')
def having_branch_copy(step, branch=None, is_patched=False):
    branch = branch or ''
    if 'system' in branch:
        branch = os.environ.get('RV_BRANCH')
    elif not branch:
        branch = os.environ.get('RV_TO_BRANCH')
    else:
        branch = branch.strip()
    world.test_branch_copy= 'test-{}/{}'.format(int(time.time()), branch)
    if is_patched:
        fixture_path = 'scripts/scalarizr_app.py'
        script_path = 'src/scalarizr/app.py'
        content = resources(fixture_path).get()
    else:
        script_path = 'README.md'
        content = 'Scalarizr\n=========\nTested build for: [%s]()' % branch
    LOG.info('Cloning branch: %s to %s' % (branch, world.test_branch_copy))
    git = GH.repos(ORG)(SCALARIZR_REPO).git
    # Get the SHA the current test branch points to
    base_sha = git.refs('heads/%s' % branch).get().object.sha
    # Create a new blob with the content of the file
    blob = git.blobs.post(
        content=base64.b64encode(content),
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
        message='Patch app.py, corrupt windows start', #TODOL Change this commit message for linux package too
        parents=[base_sha],
        tree=tree.sha)
    base_sha = commit.sha
    LOG.debug('Scalarizr service was patched. GitHub api res: %s' % commit)
    # Finally update the heads/master reference to point to the new commit
    cloned_branch = git.refs.post(ref='refs/heads/%s' % world.test_branch_copy, sha=base_sha)
    LOG.debug('New branch was created. %s' % cloned_branch)
    world.build_commit_sha = base_sha


@step(r'I wait for new package was built')
def waiting_new_package(step):
    time_until = time.time() + 1200
    error = 'Timeout or build status failed.'
    LOG.info('Getting build status for: %s' % world.build_commit_sha)
    while True:
        # Get build status
        res = GH.repos(ORG)(SCALARIZR_REPO).commits(world.build_commit_sha).status.get()
        if res.statuses:
            status = filter(lambda x: x['context'] == 'Drone', res.statuses)[0]
            LOG.debug('Patch commit build status: %s' % status)
            if status.state == 'success':
                LOG.info('Drone status: %s' % status.description)
                return
            elif status.state == 'failure':
                time_until = None
                error = 'Drone status is failed'
        if time.time() >= time_until:
            raise AssertionError(error)
        time.sleep(30)


@step(r'I have a clean image')
def having_clean_image(step):
    if Dist.is_windows_family(CONF.feature.dist):
        table = tables('images-clean')
        search_cond = dict(
            dist=CONF.feature.dist,
            platform=CONF.feature.platform)
        image_id = table.filter(search_cond).first().keys()[0].encode('ascii', 'ignore')
        image = filter(lambda x: x.id == str(image_id), world.cloud.list_images())[0]
    else:
        if CONF.feature.driver.current_cloud == Platform.EC2 and CONF.feature.dist in ['ubuntu1604', 'centos7']:
            image = world.cloud.find_image(use_hvm=True)
        else:
            image = world.cloud.find_image(use_hvm=USE_VPC)
    LOG.debug('Obtained clean image %s, Id: %s' %(image.name, image.id))
    setattr(world, 'image', image)


@step(r'I create image from deployed server')
def creating_image(step):
    cloud_server = getattr(world, 'cloud_server')
    # Create an image
    image_name = 'tmp-base-{}-{:%d%m%Y-%H%M%S}'.format(
        CONF.feature.dist,
        datetime.now()
    )
    # Set credentials to image creation
    kwargs = dict(
        node=cloud_server,
        name=image_name,
    )
    if CONF.feature.driver.is_platform_ec2:
        kwargs.update({'reboot': False})
    image = world.cloud.create_template(**kwargs)
    assert getattr(image, 'id', False), 'An image from a node object %s was not created' % cloud_server.name
    # Remove cloud server
    LOG.info('An image: %s from a node object: %s was created' % (image.id, cloud_server.name))
    setattr(world, 'image', image)
    LOG.debug('Image attrs: %s' % dir(image))
    LOG.debug('Image Name: %s' % image.name)
    if CONF.feature.driver.is_platform_cloudstack:
        forwarded_port = world.forwarded_port
        ip = world.ip
        assert world.cloud.close_port(cloud_server, forwarded_port, ip=ip), "Can't delete a port forwarding rule."
    LOG.info('Port forwarding rule was successfully removed.')
    if not CONF.feature.driver.is_platform_gce:
        assert cloud_server.destroy(), "Can't destroy node: %s." % cloud_server.id
    LOG.info('Virtual machine %s was successfully destroyed.' % cloud_server.id)
    setattr(world, 'cloud_server', None)


@step(r'I add image to the new role')
def creating_role(step):
    image_registered = False
    if CONF.feature.driver.is_platform_gce:
        cloud_location = ""
        image_id = world.image.extra['selfLink'].split('projects')[-1][1:]
    else:
         cloud_location = CONF.platforms[CONF.feature.platform]['location']
         image_id = world.image.id
    image_kwargs = dict(
        platform=CONF.feature.driver.scalr_cloud,
        cloud_location=cloud_location,
        image_id=image_id
    )
    name = 'tmp-base-{}-{:%d%m%Y-%H%M%S}'.format(
            CONF.feature.dist,
            datetime.now())
    behaviors = ['chef']
    # Checking an image
    try:
        LOG.debug('Checking an image {image_id}:{platform}({cloud_location})'.format(**image_kwargs))
        IMPL.image.check(**image_kwargs)
    except Exception as e:
        if not ('Image has already been registered' in e.message):
            raise
        image_registered = True
    if not image_registered:
        # Register image to the Scalr
        LOG.debug('Register image %s to the Scalr' % name)
        image_kwargs.update(dict(software=behaviors, name=name, is_scalarized=True))
        image = IMPL.image.create(**image_kwargs)
    # Create new role
    role_kwargs = dict(
        name=name,
        behaviors=behaviors,
        images=[dict(
            platform=CONF.feature.driver.scalr_cloud,
            cloudLocation=cloud_location,
            imageId=image_id)])
    LOG.debug('Create new role {name}. Role options: {behaviors} {images}'.format(**role_kwargs))
    role = IMPL.role.create(**role_kwargs)
    setattr(world, 'role', role['role'])


@step(r'I add created role to the farm')
def setting_farm(step):
    farm = world.farm
    branch = CONF.feature.to_branch
    release = branch in ['latest', 'stable']
    role_kwargs = dict(
        location=CONF.platforms[CONF.feature.platform]['location'] \
            if not CONF.feature.driver.is_platform_gce else "",
        options={
            "user-data.scm_branch": '' if release else branch,
            "base.upd.repository": branch if release else '',
            "base.devel_repository": '' if release else CONF.feature.ci_repo
        },
        alias=world.role['name'],
        use_vpc=USE_VPC
    )
    if CONF.feature.driver.is_platform_ec2 and Dist.is_windows_family(CONF.feature.dist):
        role_kwargs['options']['instance_type'] = 'm3.medium'
    LOG.debug('Add created role to farm with options %s' % role_kwargs)
    farm.add_role(world.role['id'], **role_kwargs)
    farm.roles.reload()
    farm_role = farm.roles[0]
    setattr(world, '%s_role' % world.role['name'], farm_role)


@step(r'I trigger scalarizr update by Scalr UI on ([\w\d]+)$')
def updating_scalarizr_by_scalr_ui(step, serv_as):
    server = getattr(world, serv_as)
    for i in range(3):
        try:
            res = IMPL.server.update_scalarizr(server_id=server.id)
            LOG.debug('Scalarizr update was fired: %s ' % res['successMessage'])
            break
        except Exception as e:
            LOG.error('Scalarizr update status: %s ' % e.message)
            time.sleep(15)
    else:
        raise Exception("Scalarizr update failed 3 times with error: %s" % e)


@step(r'scalarizr version (is default|was updated) in ([\w\d]+)$')
def asserting_version(step, version, serv_as):
    server = getattr(world, serv_as)
    default_installed_agent = getattr(world, 'default_agent', None)
    pre_installed_agent = world.pre_installed_agent
    server.reload()
    command = 'scalarizr -v'
    err_msg = 'Scalarizr version not valid %s:%s'
    # Windows handler
    if Dist.is_windows_family(CONF.feature.dist):
        res = world.run_cmd_command_until(command, server=server, timeout=300).std_out
    # Linux handler
    else:
        node = world.cloud.get_node(server)
        res = node.run(command)[0]
    installed_agent = re.findall('(?:Scalarizr\s)([a-z0-9/./-]+)', res)
    assert installed_agent , "Can't get scalarizr version: %s" % res
    installed_agent = installed_agent[0]
    if default_installed_agent:
        assert  LooseVersion(default_installed_agent) == LooseVersion(installed_agent), \
            err_msg % (default_installed_agent, installed_agent)
        world.default_agent = None
        return
    assert LooseVersion(pre_installed_agent) != LooseVersion(installed_agent), \
        err_msg % (pre_installed_agent, installed_agent)
    LOG.debug('Scalarizr was updated. Pre: %s, Inst: %s' %
              (pre_installed_agent, installed_agent))


@step(r"I (check|save) current Scalr update client version(?: was changed)? on ([\w\d]+)")
def checking_upd_client_version(step, action, serv_as):
    server = getattr(world, serv_as)
    server.reload()
    upd_client_staus = server.upd_api.status()
    LOG.info('Scalr upd client status: %s' % upd_client_staus)
    if action == 'save':
        world.upd_client_version = upd_client_staus['service_version']
        LOG.info("Current Scalr update client version: %s" % world.upd_client_version)
        return
    upd_client_version = getattr(world, 'upd_client_version')
    upd_client_current_version = upd_client_staus['service_version']
    assert LooseVersion(upd_client_current_version) > LooseVersion(upd_client_version), \
        "Scalr update client version not valid curr: %s prev: %s" % (upd_client_current_version, upd_client_version)


@step(r'I reboot server')
def rebooting_server(step): #FIXME: Find usages and rename this step
    if not world.cloud_server.reboot():
        raise AssertionError("Can't reboot node: %s" % world.cloud_server.name)
    world.cloud_server = None


@step(r"I forbid ([\w]+\s)?scalarizr update at startup and run it on ([\w\d]+)$")
def executing_scalarizr(step, pkg_type='', serv_as=None):
    # Create ScalrUpd Client status file
    if pkg_type.strip() == 'legacy':
        cwd = 'c:\Program Files\Scalarizr\Python27'
        env = '''$env:PYTHONPATH = """$env:ProgramFiles\Scalarizr\src"""; '''
    else:
        cwd = 'C:\opt\scalarizr\current\embedded'
        env = ''
    set_status = '''{env}cd """{cwd}"""; ''' \
        '''./python -m scalarizr.updclient.app --make-status-file;'''.format(env=env,cwd=cwd)
    # Run scalarizr
    run_scalarizr = '''Set-Service """ScalrUpdClient""" -startuptype manual; ''' \
        '''Set-Service """Scalarizr""" -startuptype auto; ''' \
        '''Start-Service """Scalarizr"""'''
    server = getattr(world, serv_as.strip())
    server.reload()
    kwargs = dict(server=server, timeout=300)
    assert not world.run_cmd_command_until(
        world.PS_RUN_AS.format(command=set_status),
        **kwargs).std_err, 'Scalr UpdClient status file creatoin failed'
    assert not world.run_cmd_command_until(
        world.PS_RUN_AS.format(command=run_scalarizr),
        **kwargs).std_err, 'Scalarizr execution failed'


@step(r'([\w]+) process is(?: (not))? running on ([\w\d]+)')
def checking_service_state(step, service, is_not, serv_as):
    def get_object(obj, args):
        if len(args) == 1:
            return getattr(obj, args[0])
        return get_object(getattr(obj, args[0]), args[1:])
    service_api = dict(scalarizr='api.system.dist', updclient='upd_api.status')
    server = getattr(world, serv_as)
    try:
        res = get_object(server, service_api[service].split('.'))()
    except URLError as e:
        LOG.error('Got an error while try to get %s status. Err: %s' % (service, e.reason))
        res = False
    assert (res and not is_not) or (not res and is_not), '%s service state not valid' % service


@after.each_scenario
def remove_temporary_data_after_each(scenario):
    use_afret_scenario = ['allow_clean_data']
    use_on_fail = ['allow_clean_on_fail']
    if (scenario.matches_tags(use_afret_scenario) and scenario.passed) or \
            (scenario.matches_tags(use_on_fail) and scenario.failed):
        clear_farm()
        remove_temporary_role()
    remove_temporary_branch()


def clear_farm():
    if getattr(world, 'farm', None):
        IMPL.farm.clear_roles(world.farm.id)
        LOG.info('Farm: %s was cleared' % world.farm.id)


def remove_temporary_role():
    if getattr(world, 'role', None):
        IMPL.role.delete(world.role['id'])
        LOG.info('Temporary role : %s was removed' % world.role['name'])
        IMPL.image.delete(world.role['images'][0]['extended']['hash'])
        LOG.info('Temporary image : %s was removed' % world.role['images'][0]['extended']['name'])


def remove_temporary_branch():
    # Delete github reference(cloned branch)
    if getattr(world, 'test_branch_copy', None):
        try:
            GH.repos(ORG)(SCALARIZR_REPO).git.refs('heads/%s' % world.test_branch_copy).delete()
            LOG.debug('Branch %s was deleted.' % world.test_branch_copy)
        except github.ApiError as e:
            LOG.error(e.message)
