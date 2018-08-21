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

    def __init__(self, name, location=None, instance_type=None, network=None, zone=None):
        self.instance_type = instance_type
        self.location = location
        self.network = network
        self._name = name
        self.zone = zone

    def __repr__(self):
        return str(self._name)


class Platform(object):

    AZURE = PlatformStore('azure', 'eastus', 'Standard_A1')
    CISCO = PlatformStore('cisco')
    CLOUDSTACK = PlatformStore('cloudstack', 'CSRP03', '9704e6fa-e2c3-4fb1-aa20-fc215adfb6db')
    EC2 = PlatformStore('ec2', 'us-east-1', 't2.small')
    GCE = PlatformStore('gce', 'us-central1', 'n1-standard-1', 'scalr-labs/global/networks/default', 'us-central1-a')
    HPCLOUD = PlatformStore('hpcloud')
    IDCF = PlatformStore('idcf')
    MIRANTIS = PlatformStore('mirantis')
    NEBULA = PlatformStore('nebula')
    OPENSTACK = PlatformStore('openstack', 'RegionOne', '2')
    OCS = PlatformStore('ocs')
    RACKSPACENGUK = PlatformStore('rackspacenguk')
    RACKSPACENGUS = PlatformStore('rackspacengus', 'DFW', '3')
    VIO = PlatformStore('vio')
    VMWARE = PlatformStore('vmware', 'datacenter-21', '2eb93579efde')
    INVALID = PlatformStore('invalid', 'invalid', 'invalid', 'invalid', 'invalid')


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

