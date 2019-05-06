#!/usr/bin/env python3

import os
import sys
import subprocess

import click

CHROMEDRIVER_VERSION = '2.46'
GECKODRIVER_VERSION = '0.24.0'


def green(s):
    return click.style(s, fg='green')


def yellow(s):
    return click.style(s, fg='yellow')


def red(s):
    return click.style(s, fg='red')


def local(command, log=True):
    out = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if log:
        print(out.stdout.decode())
        print(green(out.stderr.decode()))
    return out


@click.group()
def tests():
    pass


@tests.command(name='drivers')
def install_selenium_drivers():
    """Install geckodriver and chromedriver for local machine selenium runs."""
    if sys.platform == 'darwin':
        urls = [
            f'https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_mac64.zip',
            f'https://github.com/mozilla/geckodriver/releases/download/v{GECKODRIVER_VERSION}/geckodriver-v{GECKODRIVER_VERSION}-macos.tar.gz',
        ]

    elif sys.platform == 'linux':
        urls = [
            f'https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_linux64.zip',
            f'https://github.com/mozilla/geckodriver/releases/download/v{GECKODRIVER_VERSION}/geckodriver-v{GECKODRIVER_VERSION}-linux64.tar.gz']
    else:
        raise NotImplementedError(
            'Your OS is not MacOS or Linux type. You need to install chromedriver and geckodriver manually.')
    for url in urls:
        name = 'chromedriver' if 'chromedriver' in url else 'geckodriver'
        local(f'wget {url}')
        local('tar -xvzf %s*' % url.split('/')[-1])
        local('chmod +x %s' % name)
        local('rm -rf %s' % url.split('/')[-1])
        local('mv {0} /usr/local/bin/{0}'.format(name))


@tests.command(name='grid', help='Run selenium grid cluster')
@click.option('--port', default=4444, help='Port for selenium grid')
def run_grid(port):
    if 'selenium-hub' not in local('docker ps -a').stdout.decode():
        docker_networks = local('docker network ls').stdout.decode()
        if 'grid' not in docker_networks.stdout:
            local('docker network create grid')
        grid_cmd = """
            docker run -d -p {port}:{port} --name selenium-hub selenium/hub &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-chrome &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-firefox""".format(port=port)
        local(grid_cmd)


@tests.command(name='webtests', help='Run all webtests in selected browser')
@click.option('--test', default=None, help='Select one test or all')
@click.option('--browser', default='all', help='Which browser use')
@click.option('--te-id', help='Container ID')
@click.option('--te-remove', is_flag=True, help='Remove test env after tests')
@click.option('--local', '-l', 'is_local', is_flag=True, help='Run tests on local browser')
@click.option('--debug', is_flag=True, help='Change log level to debug')
def run_webtests(test, browser, te_id, te_remove, is_local, debug):
    testpath = test if test else 'ui/tests'
    browsers = ['firefox', 'chrome'] if browser == 'all' else browser
    te_id = '--te-id %s' % te_id if te_id else ''
    te_remove = '--te-remove true' if te_remove else ''
    log_level = '--log-cli-level DEBUG' if debug else ''
    if is_local:
        for browser in browsers:
            local(f'py.test --driver={browser} --disable-warnings {log_level} {te_id} {te_remove} {testpath}')
    else:
        for browser in browsers:
            local(f'py.test --driver=Remote --host 0.0.0.0 --port 4444 --capability browserName {browser} {log_level}'
                  f' --disable-warnings {te_id} {te_remove}  {testpath}')


@tests.command(name='build', help='Build docker container')
@click.option('--token', required=True, help='GitHub access token to revizor repo')
@click.option('--push', is_flag=True, default=False, help='Push to github or not')
def build_container(token, push):
    branch = local('git status', log=False).stdout.splitlines()[0].split()[-1]
    print(f'Build image for branch {branch}')
    local(f'docker build -t gcr.io/scalr-labs/revizor-tests/{branch.lower()}:latest . --build-arg TOKEN={token}')
    if push:
        print(f'Push image gcr.io/scalr-labs/revizor-tests/{branch.lower()}:latest')
        local(f'docker push gcr.io/scalr-labs/revizor-tests/{branch.lower()}:latest')


@tests.command(name='runjob', help='Run job from revizor')
def run_job():
    print('Run job successfully run!')
    print('Job ID: %s' % os.environ.get('REVIZOR_TESTSUITE_ID'))
    print('------')
    print('All env: %s' % os.environ)


if __name__ == '__main__':
    tests()
