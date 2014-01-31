__author__ = 'gigimon'

import os
import time
import logging
import subprocess

import requests
from lettuce import world, step

from revizor2.conf import CONF
from revizor2.consts import Dist

LOG = logging.getLogger(__name__)


SCALARIZR_GITHUB_PATH = 'git@github.com:Scalr/int-scalarizr.git'
SCALARIZR_REPO_PATH = '/tmp/revizor_%s/int-scalarizr' % int(time.time())

BUILDBOT_URL = 'http://buildbot.scalr-labs.com:8010'


@step('I remember scalarizr version on ([\w\d]+)$')
def remember_scalarizr_version(step, serv_as):
    server = getattr(world, serv_as)
    version = server.upd_api.status(cached=False)['installed']
    LOG.info('Remember Scalarizr version (%s) on server %s' % (version, server.id))
    setattr(world, '%s_last_scalarizr' % serv_as, version)


@step('scalarizr version is the same on ([\w\d]+)$')
def remember_scalarizr_version(step, serv_as):
    server = getattr(world, serv_as)
    version = server.upd_api.status(cached=False)['installed']
    LOG.info('Verify scalarizr version %s with old version' % version)
    if not version == getattr(world, '%s_last_scalarizr' % serv_as):
        raise AssertionError('Scalarizr version after update not same as before: %s != %s'
                             % (version, getattr(world, '%s_last_scalarizr' % serv_as)))


@step('I have reverted and working branch')
def verify_repository_is_working(step):
    if Dist.is_centos_family(Dist.from_name(CONF.feature.dist)):
        branch = 'test/update-system-rpm'
        commits = ["@update-system @rpm @postinst", "@update-system @rpm @fatal-error"]
    elif Dist.is_debian_family(Dist.from_name(CONF.feature.dist)):
        branch = 'test/update-system-deb'
        commits = ["@update-system @deb @postinst", "@update-system @deb @fatal-error"]
    elif CONF.feature.dist.startswith('win'):
        branch = 'test/update-system-win'
        commits = ["@update-system @win @postinst", "@update-system @win @fatal-error"]
    else:
        raise AssertionError('Don\'t know what branch use!')
    LOG.info('Used scalarizr branch is %s' % branch)
    setattr(world, 'scalarizr_branch', branch)

    if not os.path.isdir(SCALARIZR_REPO_PATH):
        LOG.info('Clone scalarizr repo')
        exit_code = subprocess.call(['git', 'clone', '-b', branch, SCALARIZR_GITHUB_PATH, SCALARIZR_REPO_PATH],
                                    stderr=subprocess.PIPE)
        if not exit_code == 0:
            raise AssertionError('Error in git clone!')

    os.chdir(SCALARIZR_REPO_PATH)

    git_log = subprocess.check_output(['git', 'log', '--pretty=oneline', '-20']).splitlines()
    LOG.info('Get latest commits from git history: %s' % git_log)
    flags = {}
    for log in git_log:
        commit, message = log.split(' ', 1)
        message = message.strip()
        for m in commits:
            if message.startswith('Revert "%s"' % m) or message.startswith("Revert '%s'" % m):
                flags[m] = True
            elif message.startswith(m) and not flags.get(m, False):
                # revert last commit
                LOG.info('Revert broken commit "%s %s"' % (commit, message))
                subprocess.call(['git', 'revert', commit, '-n', '--no-edit'])
                subprocess.call(['git', 'commit', '-a', '-m', "Revert '%s'" % message])
                subprocess.call(['git', 'push'])
                flags[m] = True
        if len(flags) == len(commits):
            return


@step('I broke branch with commit "(.+)"$')
def broke_scalarizr_branch(step, comment):
    LOG.debug('Git work dir: %s' % SCALARIZR_REPO_PATH)
    os.chdir(SCALARIZR_REPO_PATH)

    if Dist.is_centos_family(Dist.from_name(CONF.feature.dist)):
        tag = '@rpm'
    elif Dist.is_debian_family(Dist.from_name(CONF.feature.dist)):
        tag = '@deb'
    elif CONF.feature.dist.startswith('win'):
        tag = '@win'

    comment = comment.split()
    comment.insert(-1, tag)
    comment = ' '.join(comment)

    command = ['git', 'log', '--pretty=oneline', '--grep=Revert "%s"' % comment]
    LOG.debug('Execute grep by git: %s' % command)
    git_log = subprocess.check_output(command, stderr=subprocess.PIPE).strip().splitlines()
    LOG.info('Get latest commits from git history (in broke step): %s' % git_log)
    commit, message = git_log[0].split(' ', 1)
    LOG.info('Revert commit "%s %s" for brake repository' % (commit, message))
    subprocess.call(['git', 'revert', commit, '-n', '--no-edit'])
    subprocess.call(['git', 'commit', '-a', '-m', '%s' % message])
    subprocess.call(['git', 'push'])


@step('new package is builded')
def verify_package_is_builded(step):
    LOG.info('Wait last scalarizr source builder in buildbot finish work')
    while True:
        resp = requests.get('%s/json/builders/scalarizr%%20source' % BUILDBOT_URL).json()
        if not resp['state'] == 'idle':
            time.sleep(15)
            continue
        return
        #latest_build = resp['cachedBuilds'][-1]
        #break
    #build = requests.get('%s/json/builders/scalarizr%%20source/builds/%s' % (BUILDBOT_URL, latest_build)).json()
    #for prop in build['properties']:
    #    if prop[0] == 'normalized_branch' and prop[1] == world.scalarizr_branch:
    #        return
    #raise AssertionError('Last build in buildbot not from this branch')


@step('I update scalarizr via api on ([\w\d]+)')
def update_scalarizr_via_api(step, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Update scalarizr bi Scalarizr update API on server %s' % server.id)
    server.upd_api.update(async=True)


@step('update process is finished on ([\w\d]+) with status (\w+)')
def wait_updating_finish(step, serv_as, status):
    server = getattr(world, serv_as)
    start_time = time.time()
    while int(time.time()-start_time) < 600:
        try:
            LOG.info('Verify update process is finished')
            result = server.upd_api.status()
            if result['state'].startswith(status):
                LOG.info('Update process finished with waited status: %s' % result['state'])
                return
            elif not status == 'error' and result['state'].startswith('error'):
                raise AssertionError('Update process failed with error: %s' % result['error'])
            else:
                LOG.info('Update process on server %s in "%s" state, wait status %s' % (server.id, result['state'], status))
                time.sleep(5)
        except:
            time.sleep(15)