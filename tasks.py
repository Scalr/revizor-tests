from invoke import task

PYENV_ROOT = '/usr/local/pyenv'
PYENV_PROFILE = '/etc/profile.d/pyenv.sh'
PIP_VERSION = '10.0.1'
PIP_TOOLS_VERSION = '1.9.0'
PY_VERSIONS = ['3.6.5']


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
            docker run -d -P -p 6001:5900 --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-chrome-debug &&
            docker run -d -P -p 5901:5900 --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-firefox-debug""".format(port=port)
        ctx.run(grid_cmd)


@task(grid)
def webtests(ctx, testpath='', browsers='all', processes=''):
    """Incrementally executes speicified selenium/pytest test cases with specified browsers.

       :param str testpath: path to specific pytest modules or folders with tests.
        Usage: '--testpath /vagrant/selenium/.../test.py'.
       :param str browsers: list of browsers on which the test should be executed.
        Usage: '--browsers firefox,chrome,...'.
       :param str processes: number of processes for parallel testing.
        Usage: '--processes 3'.
    """
    browsers = ['firefox', 'chrome'] if browsers == 'all' else browsers.split(',')
    processes = ' -n %s' % processes if processes else ''
    for browser in browsers:
        command = 'python -m pytest%s --driver Remote --host 0.0.0.0 --port 4444 --capability browserName %s %s' %\
            (processes, browser, testpath)
        print(command)
        ctx.run(command)
