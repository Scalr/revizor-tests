import logging

from lettuce import world, step

from revizor2.api import IMPL

LOG = logging.getLogger(__name__)
PLUGIN_NAME = 'scalr-auth'
SPEC_PATH = '/etc/docker/plugins/%s.spec' % PLUGIN_NAME
CONF_PATH = '/etc/docker/daemon.json'
VALIDATIONS = {
    'escalating': {
        'cmd': 'docker stop rev1'
               '; docker rm rev1'
               '; docker run -d --name rev1 spotify/alpine /bin/sh -c \'while :; do echo .; sleep 1; done\''
               ' && docker exec --privileged rev1 /bin/sh -c \'sleep 1s\'',
        'err': 'authorization denied by plugin scalr-auth: Privileged mode is not allowed',
        'code': 1
    }
    ,
    'privileged': {
        'cmd': 'docker run --privileged spotify/alpine',
        'err': 'authorization denied by plugin scalr-auth: Privileged mode is not allowed',
        'code': 125
    },
    'sources': {
        'cmd': 'docker run alpine',
        'err': 'authorization denied by plugin scalr-auth: It\'s not allowed to create this image',
        'code': 125
    },
    'ports': {
        'cmd': 'docker run -p 81:81 spotify/alpine',
        'err': 'authorization denied by plugin scalr-auth: It\'s not allowed to bind the 81 port',
        'code': 125
    },
    'mounts': {
        'cmd': 'docker run -v /etc:/etc spotify/alpine',
        'err': 'authorization denied by plugin scalr-auth: The directory /etc is forbidden to mount',
        'code': 125
    }
}


@step("docker-authz plugin is( not)? installed on ([\w\d]+)")
def check_authz_plugin_presence(step, expected, server_as):
    expected = not bool(expected)
    server = getattr(world, server_as)
    node = world.cloud.get_node(server)
    command = '[ -f %s ] && grep -q %s %s' % (SPEC_PATH, PLUGIN_NAME, CONF_PATH)
    is_installed = not node.run(command).status_code
    if is_installed != expected:
        raise AssertionError('Docker authz plugin installation status is incorrect.'
                             ' Expected="%sinstalled", actual="%sinstalled"' %
                             ('' if expected else 'not ', '' if is_installed else 'not '))


@step("([\w,]+) policies( do not)? work on ([\w\d]+)")
def validate_policy(step, policy_names, expected, server_as):
    expected = not bool(expected)
    server = getattr(world, server_as)
    node = world.cloud.get_node(server)
    if policy_names == 'all':
        policies = VALIDATIONS.keys()
    else:
        policies = policy_names.split(',')
    with node.remote_connection() as conn:
        for policy in policies:
            _validate_policy(conn, policy, expected)


def _validate_policy(connection, policy_name, expected):
    result = connection.run(VALIDATIONS[policy_name]['cmd'])
    works = VALIDATIONS[policy_name]['err'] in result.std_err \
            and result.status_code == VALIDATIONS[policy_name]['code']
    if works != expected:
        raise AssertionError('Validation failed for "%s" policy.'
                             ' Expected="%s", actual="%s"'
                             ' (std_err="%s", status_code="%s").' %
                             (policy_name,
                              'works' if expected else 'does not work',
                              'works' if works else 'does not work',
                              result.std_err, result.status_code))
