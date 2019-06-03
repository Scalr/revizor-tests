#!/usr/bin/env python3

import os
import sys
import subprocess

import click
import requests

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


def get_gcloud_project():
    print('Get current google project')
    return local('gcloud config get-value project').stdout.decode().strip().replace(':', '/')


@click.group()
def tests():
    pass


@tests.command(name='drivers')
def install_selenium_drivers():
    """Install geckodriver and chromedriver for local machine selenium runs."""
    if sys.platform == 'darwin':
        urls = [
            f'https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_mac64.zip',
            f'https://github.com/mozilla/geckodriver/releases/download/'
            f'v{GECKODRIVER_VERSION}/geckodriver-v{GECKODRIVER_VERSION}-macos.tar.gz',
        ]

    elif sys.platform == 'linux':
        urls = [
            f'https://chromedriver.storage.googleapis.com/{CHROMEDRIVER_VERSION}/chromedriver_linux64.zip',
            f'https://github.com/mozilla/geckodriver/releases/download/'
            f'v{GECKODRIVER_VERSION}/geckodriver-v{GECKODRIVER_VERSION}-linux64.tar.gz']
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
    branch = local('git status', log=False).stdout.decode().splitlines()[0].split()[-1].lower().replace('/', '-')
    project = get_gcloud_project()
    print(f'Build image for branch {branch} and project {project}')
    res = local(f'docker build -t gcr.io/{project}/revizor-tests/{branch}:latest . --build-arg TOKEN={token}')
    if res.returncode != 0:
        print(red('Build failed!'))
        sys.exit(1)
    if push:
        print(f'Push image gcr.io/{project}/revizor-tests/{branch}:latest')
        local(f'docker push gcr.io/{project}/revizor-tests/{branch}:latest')


@tests.command(name='runjob', help='Run job from revizor')
def run_job():
    print('Run job from revizor')
    token = os.environ.get('REVIZOR_API_TOKEN')
    if not token:
        print('You must provide revizor api token to run tests!')
        sys.exit(0)
    revizor_url = os.environ.get('REVIZOR_URL', 'https://revizor.scalr-labs.com')
    testsuite_id = os.environ.get('REVIZOR_TESTSUITE_ID')
    test = requests.get(f'{revizor_url}/api/tests/retrieve/{testsuite_id}', headers={'Authorization': f'Token {token}'})
    if test.status_code == 404:
        print(red(f'Tests not found for {testsuite_id} test suite!'))
        sys.exit(0)

    body = test.json()
    os.environ['REVIZOR_TESTINSTANCE_ID'] = str(body['id'])
    command = body['params']  #FIXME: Automate this in surefire side?
    command += ' --report-surefire'

    print(f'Start test with command "{command}"')
    process = subprocess.run(command, shell=True)

    status = 'COMPLETED'
    if process.returncode != 0:
        status = 'FAILED'
    print('Report test status')
    resp = requests.post(f'{revizor_url}/api/tests/result/{body["id"]}', headers={'Authorization': f'Token {token}'},
                         json={'status': status})
    print(resp.text)


if __name__ == '__main__':
    tests()