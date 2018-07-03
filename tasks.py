from invoke import task

PYENV_ROOT = '/usr/local/pyenv'
PYENV_PROFILE = '/etc/profile.d/pyenv.sh'
PIP_VERSION = '10.0.1'
PIP_TOOLS_VERSION = '1.9.0'
PY_VERSIONS = ['3.6.5']


@task
def grid(ctx, docs=False, port='4444'):
    if 'selenium-hub' not in ctx.run('docker ps -a').stdout:
        docker_networks = ctx.run('docker network ls')
        if 'grid' not in docker_networks.stdout:
            ctx.run('docker network create grid')
        grid_cmd = """
            docker run -d -p {port}:{port} --name selenium-hub selenium/hub &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-chrome &&
            docker run -d --link selenium-hub:hub -v /dev/shm:/dev/shm selenium/node-firefox""".format(port=port)
        ctx.run(grid_cmd)


@task(grid)
def webtests(ctx, test_cases='', browsers='all', processes=''):
    browsers = ['firefox', 'chrome'] if browsers == 'all' else browsers.split(',')
    processes = ' -n %s' % processes if processes else ''
    for browser in browsers:
        command = 'python -m pytest%s --driver Remote --host 0.0.0.0 --port 4444 --capability browserName %s %s' % (processes, browser, test_cases)
        print(command)
        ctx.run(command)
