import sys
import os

from invoke import task

PYENV_ROOT = '/usr/local/pyenv'
PYENV_PROFILE = '/etc/profile.d/pyenv.sh'
PIP_VERSION = '10.0.1'
PIP_TOOLS_VERSION = '1.9.0'
PY_VERSIONS = ['3.6.5']
CHROMEDRIVER_VERSION = '2.44'
GECKODRIVER_VERSION = '0.23.0'


@task
def grid(ctx, docs=False, port='4444'):
    """Starts Selenium HUB, firefox node and chrome node docker containers,
       if they're not already running.
       Creates 'grid' docker network unless already exists.

       :param str port: selenium hub port.
    """
    if 'selenium-hub' not in ctx.run('docker ps -a').stdout:
        docker_networks = ctx.run('docker network ls')
        if 'grid' not in docker_networks.stdout:
            ctx.run('docker network create grid')
        grid_cmd = """
            docker run -d -p {port}:{port} --name selenium-hub selenium/hub &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-chrome &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-firefox""".format(port=port)
        ctx.run(grid_cmd)


@task(help={
    'testpath': "Path to specific pytest modules or folders with tests to run.",
    'browsers': "List of browsers to run tests with.",
    'processes': "Specify number of processes for parallel testing.",
    'te-id': "Id of the specific TestEnv you want your tests to run on.",
    'localmode': "Run tests on local machine using selenium drivers directly insted of docker containers.",
    'te-remove': "If specified, TestEnv will be deleted at the end of test session, even if some tests will fail.",
    'debug-mode': "Print logged messages of specified level as they appear during test run. Possible levels DEBUG, INFO, WARNING, ERROR. Default level INFO."
})
def webtests(ctx, testpath=None, browsers='all', processes=None, te_id=None, localmode=None, te_remove=None, debug_mode='INFO'):
    """Incrementally executes speicified selenium/pytest test cases with specified browsers.
    """
    testpath = testpath if testpath else ''
    browsers = ['firefox', 'chrome'] if browsers == 'all' else browsers.split(',')
    processes = ' -n %s' % processes if processes else ''
    te_id = '--te-id %s' % te_id if te_id else ''
    te_remove = '--te-remove true' if te_remove else ''
    debug_mode = '--log-cli-level %s' % debug_mode.upper()
    for browser in browsers:
        driver = browser if localmode else 'Remote'
        command = 'python3 -m pytest%s %s --driver %s --host 0.0.0.0 --port 4444 --capability browserName %s %s %s %s --disable-warnings' %\
            (processes, debug_mode, driver, browser, testpath, te_id, te_remove) #FIX ME - Deals with using deprecated options in third-party libraries (mainly pluggy)
        print(command)
        ctx.run(command)


@task
def seleniumdrivers(ctx):
    """Install geckodriver and chromedriver for local machine selenium runs.
    """
    if sys.platform == 'darwin':
        urls = [
            'https://chromedriver.storage.googleapis.com/%s/chromedriver_mac64.zip' % CHROMEDRIVER_VERSION,
            'https://github.com/mozilla/geckodriver/releases/download/%s/geckodriver-v%s-macos.tar.gz' % GECKODRIVER_VERSION]
    elif sys.platform == 'linux':
        urls = [
            'https://chromedriver.storage.googleapis.com/%s/chromedriver_linux64.zip' % CHROMEDRIVER_VERSION,
            'https://github.com/mozilla/geckodriver/releases/download/v%s/geckodriver-v%s-linux64.tar.gz' % GECKODRIVER_VERSION]
    else:
        raise NotImplementedError('Your OS is not MacOS or Linux type. You need to install chromedriver and geckodriver manually.')
    for url in urls:
        name = 'chromedriver' if 'chromedriver' in url else 'geckodriver'
        ctx.run('wget %s' % url)
        ctx.run('tar -xvzf %s*' % url.split('/')[-1])
        ctx.run('chmod +x %s' % name)
        ctx.run('rm -rf %s' % url.split('/')[-1])
        ctx.run('mv {0} /usr/local/bin/{0}'.format(name))
