# coding: utf-8
"""
Created on 01.08.18
@author: Eugeny Kurkovich
"""

ENV_ID = 5
COST_PROJECT_ID = "30c59dba-fc9b-4d0f-83ec-4b5043b12f72"


class APIParams(object):

    request_types = {
        'create': 'post',
        'delete': 'delete',
        'edit': 'patch',
        'list': 'get',
        'get': 'get',
        'fire': 'post',
        'import_server': 'post',
        'clone': 'post',
        'generate_template': 'get',
        'launch': 'post',
        'lock': 'post',
        'resume': 'post',
        'suspend': 'post',
        'terminate': 'post',
        'unlock': 'post',
        'copy': 'post',
        'replace': 'post',
        'deprecate': 'post',
        'promote': 'post',
        'create_rule': 'post',
        'delete_rule': 'delete',
        'edit_rule': 'patch',
        'edit_scaling_configuration': 'patch',
        'get_rule': 'get',
        'get_scaling_configuration': 'get',
        'execute': 'post',
        'reboot': 'post'
    }

    response_data_types = {
        'string': '',
        'boolean': True,
        'integer': 1,
        'number': 1,
        'array': []
    }


class PlatformStore(object):

    def __init__(self, name, **kwargs):
        self._name = name
        self.__dict__.update(**kwargs)

    def __repr__(self):
        return str(self._name)

    def __getattr__(self, attr):
        if attr.startswith('is'):
            platform = attr.split('_')[-1]
            return platform == self._name
        super().__getattribute__(attr)

    def __eq__(self, other):
        return other == self._name


class Platform(object):

    AZURE = PlatformStore(name='azure',
                          location='eastus',
                          instance_type='Standard_A1',
                          network='/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/'
                                  'resourceGroups/revizor/providers/Microsoft.Network/'
                                  'virtualNetworks/revizor',
                          zone='/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/'
                               'resourceGroups/revizor/providers/Microsoft.Compute/'
                               'availabilitySets/revizor',
                          subnet='/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/'
                                 'resourceGroups/revizor/providers/Microsoft.Network/'
                                 'virtualNetworks/revizor/subnets/revizor',
                          resource_group='/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/'
                                         'resourceGroups/revizor',
                          storage_account='/subscriptions/6276d188-6b35-4b44-be1d-12633d236ed8/'
                                          'resourceGroups/revizor/providers/Microsoft.Storage/'
                                          'storageAccounts/revizor')

    CLOUDSTACK = PlatformStore(name='cloudstack',
                               location='CSRP03',
                               instance_type='9704e6fa-e2c3-4fb1-aa20-fc215adfb6db',
                               network='bbb69489-35c2-45e0-b416-850eb19fcd2e')

    EC2 = PlatformStore(name='ec2',
                        location='us-east-1',
                        instance_type='t2.small',
                        network='vpc-596aa03e')

    GCE = PlatformStore(name='gce',
                        location='us-central1',
                        instance_type='n1-standard-1',
                        network='scalr-labs/global/networks/default',
                        zone='us-central1-a')

    OPENSTACK = PlatformStore(name='openstack',
                              location='RegionOne',
                              instance_type='2',
                              network='9d001c2f-3960-46cb-aef4-8bbc96500958')

    RACKSPACENGUS = PlatformStore(name='rackspacengus',
                                  location='DFW',
                                  instance_type='3',
                                  network='00000000-0000-0000-0000-000000000000')

    VMWARE = PlatformStore(name='vmware',
                           location='datacenter-21',
                           instance_type='2eb93579efde',
                           network='network-104',
                           folder='group-v22',
                           compute_resource='domain-c35',
                           host='host-442',
                           resource_pool='resgroup-36',
                           data_store='datastore-443')

    INVALID = PlatformStore(name='invalid',
                            location='invalid',
                            instance_type='invalid',
                            network='invalid',
                            zone='invalid')

class BuiltInAutomation(object):

    BASE = 'base'
    CHEF = 'chef'
    MYSQL = 'mysql'
    POSTGRESQL = 'postgresql'
    PEERCONA = 'percona'
    APACHE = 'apache'
    TOMCAT = 'tomcat'
    HAPROXY = 'haproxy'
    NGINX = 'nginx'
    MEMCACHED = 'memcached'
    REDIS = 'redis'
    RABBITMQ = 'rabbitmq'
    INVALID = 'invalid'
    UNCOMBINED_BEHAVIORS = [
        MYSQL,
        POSTGRESQL
    ]

