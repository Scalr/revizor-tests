from lettuce import step, world

from revizor2.api import IMPL

POLICIES = {
    'container': {
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
    },
    'csg': {
        'api_prefix': {
            'type': 'csg.resource.name.prefix',
            'status': 1,
            'value': {
                'conditions': {
                    'cloud': 'ec2',
                    'cloud.service': 'apigateway',
                    'service.resource': 'CreateRestApi'
                },
                'rules': [
                    {
                        'type': 'validation',
                        'value': 'tmp_'
                    }
                ]
            }
        },
        'sqs_prefix': {
            'type': 'csg.resource.name.prefix',
            'status': 1,
            'value': {
                'conditions': {
                    'cloud': 'ec2',
                    'cloud.service': 'sqs',
                    'service.resource': 'CreateQueue'
                },
                'rules': [
                    {
                        'type': 'validation',
                        'value': 'tmp_'
                    }
                ]
            }
        },
        'ecs_pattern': {
            'type': 'csg.resource.name.validation_pattern',
            'status': 1,
            'value': {
                'conditions': {
                    'cloud': 'ec2',
                    'cloud.service': 'ecs',
                    'service.resource': 'CreateCluster'
                },
                'rules': [
                    {
                        'type': 'validation',
                        'value': '/[a-z]+/i'
                    }
                ]
            }
        }
    }
}


@step("I add new (\w+) policy group '([\w\d-]+)'(?: with ([\w,]+))? as ([\w\d]+)")
def create_policy_group(step, group_type, group_name, policy_names, group_as):
    group_type = group_type.lower()
    if group_type not in POLICIES:
        raise NotImplementedError("Policy group type '%s' is not supported")
    if policy_names:
        policies = [POLICIES[group_type][p] for p in POLICIES[group_type] if p in policy_names.split(',')]
    else:  # Add all policies by default
        policies = POLICIES[group_type].values()
    group_id = IMPL.policy_groups.create(group_name, group_type, policies)
    setattr(world, 'policy_group_%s' % group_as, group_id)


@step("I delete policy group ([\w\d]+)")
def delete_policy_group(step, group_as):
    group_id = getattr(world, 'policy_group_%s' % group_as)
    IMPL.policy_groups.delete(group_id)


@step("I (link|unlink) policy group ([\w\d]+) (?:to|from) environment")
def link_policy_group(step, action, group_as):
    group_id = getattr(world, 'policy_group_%s' % group_as)
    env_id = IMPL.account.get_env()['env_id']
    if action == 'unlink':
        IMPL.environments.unlink_policy_groups(env_id, group_id)
    else:
        IMPL.environments.link_policy_groups(env_id, group_id)
