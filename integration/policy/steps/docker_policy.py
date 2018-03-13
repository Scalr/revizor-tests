import logging

from lettuce import world, step

from revizor2.api import IMPL

LOG = logging.getLogger(__name__)
PLUGIN_NAME = 'scalr-auth'
SPEC_PATH = '/etc/docker/plugins/%s.spec' % PLUGIN_NAME
CONF_PATH = '/etc/docker/daemon.json'
POLICIES = {
    'escalating': {
        'type': 'docker.container.privileged.escalating_exec_usage',
        'status': 1,
        'value': {
            'conditions': {
                'cloud': 'gce'
            },
            'rules': [
                {
                    'type': 'override',
                    'value': True
                }
            ]
        }
    },
    'privileged': {
        'type': 'docker.container.privileged.usage',
        'status': 1,
        'value': {
            'conditions': {
                'cloud': 'gce'
            },
            'rules': [
                {
                    'type': 'override',
                    'value': True
                }
            ]
        }
    },
    'sources': {
        'type': 'docker.image.sources',
        'status': 1,
        'value': {
            'conditions': {
                'cloud': 'gce'
            },
            'rules': [
                {
                    'type': 'validation',
                    'value': [
                        {
                            'source': 'spotify/alpine',
                            'type': 'registry'
                        }
                    ]
                }
            ]
        }
    },
    'ports': {
        'type': 'docker.network.ports',
        'status': 1,
        'value': {
            'conditions': {
                'cloud': 'gce'
            },
            'rules': [
                {
                    'type': 'validation',
                    'value': ['80', '8080', '443']
                }
            ]
        }
    },
    'mounts': {
        'type': 'docker.volume.mounts',
        'status': 1,
        'value': {
            'conditions': {
                'cloud': 'gce'
            },
            'rules': [
                {
                    'type': 'validation',
                    'value': ['/var/log']
                }
            ]
        }
    }
}
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


@step("I add new Container policy group '([\w\d-]+)'(?: with ([\w,]+))? as ([\w\d]+)")
def create_policy_group(step, group_name, policy_names, group_as):
    if policy_names:
        policies = [POLICIES[p] for p in POLICIES if p in policy_names.split(',')]
    else:  # Add all policies by default
        policies = POLICIES.values()
    group_id = IMPL.policy_groups.create(group_name, 'container', policies)
    setattr(world, 'policy_group_%s' % group_as, group_id)


@step("I delete policy group ([\w\d]+)")
def delete_policy_group(step, group_as):
    group_id = getattr(world, 'policy_group_%s' % group_as)
    IMPL.policy_groups.delete(group_id)


@step("I (link|unlink) policy group ([\w\d]+) (?:to|from) environment '([\w\d-]+)'")
def link_policy_group(step, action, group_as, env_name):
    group_id = getattr(world, 'policy_group_%s' % group_as)
    env_id = IMPL.account.get_env()['env_id']
    if action == 'unlink':
        IMPL.environments.unlink_policy_groups(env_id, group_id)
    else:
        IMPL.environments.link_policy_groups(env_id, group_id)


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
