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


@step('I push an empty commit to scalarizr repo$')
def bump_scalarizr_version(step):
    subprocess.call(["echo ' ' >> %s/requirements_test" % SCALARIZR_REPO_PATH], shell=True)
    os.chdir(SCALARIZR_REPO_PATH)
    subprocess.call(['git', 'commit', '-a', '-m', "Bump scalarizr version for test"])
    last_revision = subprocess.check_output(['git', 'log', '--pretty=oneline', '-1']).splitlines()[0].split()[0].strip()
    LOG.info('Last pushed revision: %s' % last_revision)
    setattr(world, 'last_scalarizr_revision', last_revision)
    out = subprocess.check_output(['git', 'push'])
    LOG.debug('Push log: %s' % out)


@step('I remember scalarizr version on ([\w\d]+)$')
def remember_scalarizr_version(step, serv_as):
    LOG.info('Kepp scalarizr version')
    server = getattr(world, serv_as)
    version = server.upd_api.status(cached=True)['installed']
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

    LOG.info('Merge feature/update-system to this repository')

    merge_proc = subprocess.Popen(['git', 'merge', '-m', 'merge parent branch', 'origin/feature/update-system'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    merge_proc.wait()
    LOG.debug('Merge process result: %s' % merge_proc.stdout.read())

    if merge_proc.returncode != 0:
        raise AssertionError('Something wrong in git merge, please see log: %s' % merge_proc.stdout.read())

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
                last_revision = subprocess.check_output(['git', 'log', '--pretty=oneline', '-1']).splitlines()[0].split()[0].strip()
                LOG.info('Last pushed revision: %s' % last_revision)
                setattr(world, 'last_scalarizr_revision', last_revision)
                flags[m] = True
        if len(flags) == len(commits):
            break
    LOG.debug('Push changes to working branch')
    subprocess.call(['git', 'push'])


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

    command = ['git', 'log', '--pretty=oneline', "--grep=Revert '%s'" % comment]
    LOG.debug('Execute grep by git: %s' % command)
    git_log = subprocess.check_output(command, stderr=subprocess.PIPE).strip().splitlines()
    if not git_log:
        command = ['git', 'log', '--pretty=oneline', '--grep=Revert "%s"' % comment]
        LOG.debug('Execute grep by git: %s' % command)
        git_log = subprocess.check_output(command, stderr=subprocess.PIPE).strip().splitlines()
    LOG.info('Get latest commits from git history (in broke step): %s' % git_log)
    splitted_log = git_log[0].split(' ', 2)
    commit = splitted_log[0]
    message = splitted_log[-1].replace('"', '').replace("'", '')
    LOG.info('Revert commit "%s %s" for brake repository' % (commit, message))
    subprocess.call(['git', 'revert', commit, '-n', '--no-edit'])
    subprocess.call(['git', 'commit', '-a', '-m', '%s' % message])
    last_revision = subprocess.check_output(['git', 'log', '--pretty=oneline', '-1']).splitlines()[0].split()[0].strip()
    LOG.info('Last pushed revision: %s' % last_revision)
    setattr(world, 'last_scalarizr_revision', last_revision)
    subprocess.call(['git', 'push'])
    time.sleep(60)


@step('new package is builded')
def verify_package_is_builded(step):
    LOG.info('Wait last scalarizr source builder in buildbot finish work')
    while True:
        resp = requests.get('%s/json/builders/scalarizr%%20source' % BUILDBOT_URL).json()
        if not resp['state'] == 'idle':
            time.sleep(15)
            continue
        for build_number in reversed(resp['cachedBuilds']):
            LOG.debug('Check for our scalarizr build: %s' % build_number)
            build = requests.get('%s/json/builders/scalarizr%%20source/builds/%s' % (BUILDBOT_URL, build_number)).json()
            if not build['sourceStamps'][0]['revision'] == world.last_scalarizr_revision:
                LOG.debug('This build has revision: %s' % build['sourceStamps'][0]['revision'])
                continue
            elif build['sourceStamps'][0]['revision'] == world.last_scalarizr_revision:
                if not world.scalarizr_branch in build['sourceStamps'][0]['branch']:
                    raise AssertionError('Last build %s not with current scalarizr branch: %s (it has %s)' %
                                (build_number, world.scalarizr_branch, build['sourceStamps'][0]['branch'])
                    )
                LOG.info('We found our build and it finished')
                return


@step('I update scalarizr via api on ([\w\d]+)')
def update_scalarizr_via_api(step, serv_as):
    server = getattr(world, serv_as)
    LOG.info('Update scalarizr by Scalarizr update API on server %s' % server.id)
    for i in range(3):
        try:
            server.upd_api.update(async=True)
            break
        except:
            LOG.debug('Try update scalarizr via api attempt %s' % i)
            time.sleep(5)


@step('update process is finished on ([\w\d]+) with status (\w+)')
def wait_updating_finish(step, serv_as, status):
    #TODO: verify scalarizr vesion by revision
    server = getattr(world, serv_as)
    start_time = time.time()
    status = status.strip()
    LOG.info('Wait status %s on update process' % status)
    while int(time.time()-start_time) < 900:
        try:
            result = server.upd_api.status(cached=True)
            if result['state'].startswith(status):
                LOG.info('Update process finished with waited status: %s' % result['state'])
                return
            elif result['state'].startswith('error') and not status == 'error':
                raise AssertionError('Update process failed with error: %s' % result['error'])
            LOG.info('Update process on server %s in "%s" state, wait status %s' % (server.id, result['state'], status))
            time.sleep(5)
        except AssertionError:
            LOG.error('Update process failed')
            raise
        except BaseException, e:
            LOG.debug('Checking update process raise exception: %s' % e)
            time.sleep(15)
    else:
        raise AssertionError('Until 10 minutes status not: %s, it: %s' % (status, result['state']))