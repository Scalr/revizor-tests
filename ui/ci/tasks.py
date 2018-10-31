import os
import shutil

from contextlib import contextmanager

from invoke import task, run

PYENV_ROOT = '/usr/local/pyenv'
PYENV_PROFILE = '/etc/profile.d/pyenv.sh'
PIP_VERSION = '10.0.1'
PIP_TOOLS_VERSION = '1.9.0'
PY_VERSIONS = ['3.6.5']


def pip_install(command):
    run('/usr/local/pyenv/shims/pip --version')
    pip = '/usr/local/pyenv/shims/pip install'
    run('sudo {} {}'.format(pip, command))


def apt_get_install(packages):
    run('apt-get install -qq -y {}'.format(packages))


def apt_get_update(options=None):
    print('apt-get update')
    command = 'apt-get update -qq'
    if options:
        command += ' {}'.format(options)
    run(command, warn=True)


def create_file(name, source=None, content=None, mode=None, owner=None):
    print('create {}'.format(name))
    if content:
        with open(name, 'w+') as fp:
            fp.write(content)
    elif source:
        if source.startswith('http://') or source.startswith('https://'):
            run('curl -sL -o {} {}'.format(name, source))
        else:
            shutil.copy(source, name)
    if mode:
        os.chmod(name, mode)
    if owner:
        run('chown {} {}'.format(owner, name))


@contextmanager
def pyenv_version(version):
    try:
        os.environ['PYENV_VERSION'] = version
        yield
    finally:
        if 'PYENV_VERSION' in os.environ:
            del os.environ['PYENV_VERSION']


@task
def pythons(ctx):
    """Install python 2 and 3
    """
    apt_get_install('make build-essential libssl-dev zlib1g-dev libbz2-dev '
                    'libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev')

    # install pyenv
    if not os.path.exists(PYENV_ROOT):
        print('install pyenv')
        ctx.run('git clone git://github.com/yyuu/pyenv.git {}'.format(PYENV_ROOT))

        with ctx.cd(PYENV_ROOT):
            # update pyenv
            print('update pyenv')
            ctx.run('git pull origin master')

    if not os.path.exists(PYENV_PROFILE):
        # create pyenv bash profile
        create_file(PYENV_PROFILE,
                    source='/vagrant/pyenv.bash_profile',
                    mode=0o644)

    # update inprocess ENV variables
    os.environ['PATH'] = '{0}/shims:{0}/bin'.format(PYENV_ROOT) + ':' + os.environ['PATH']
    os.environ['PYENV_ROOT'] = PYENV_ROOT

    # install pythons
    for version in PY_VERSIONS:
        print('install python {}'.format(version))
        if version not in ctx.run('pyenv versions').stdout:
            os.environ['PYTHON_CONFIGURE_OPTS'] = '--enable-shared --with-dbmliborder=gdbm'
            ctx.run('pyenv install {}'.format(version))
            with pyenv_version(version):
                pip_install(
                    '--upgrade pip=={} pip-tools=={}'.format(PIP_VERSION, PIP_TOOLS_VERSION))

    pip_install('ipython')


@task
def requirements(ctx, py_versions='', update=False, path='/vagrant/ui/ci/requirements.txt'):
    """Install python requirements for specific python versions or for all available
    """
    flags = ' --upgrade ' if update else ''
    py_versions = py_versions.split(',') if py_versions else PY_VERSIONS
    for version in py_versions:
        print('install {} requirements'.format(version))
        with pyenv_version(version):
            pip_install(
                ' -r {} {}'.format(path, flags)
            )