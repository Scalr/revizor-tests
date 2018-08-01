# coding: utf-8
"""
Created on 01.08.18
@author: Eugeny Kurkovich
"""

class Defaults(object):

    request_types = {
        'create': 'post',
        'delete': 'delete',
        'edit': 'patch',
        'list': 'get',
        'get': 'get'
    }

    response_data_types = {
        'string': '',
        'boolean': True,
        'integer': 1,
        'number': 1,
        'array': []
    }


class Platform(object):

    AZURE = 'azure'
    CISCO = 'cisco'
    CLOUDSTACK = 'cloudstack'
    EC2 = 'ec2'
    GCE = 'gce'
    HPCLOUD = 'hpcloud'
    IDCF = 'idcf'
    MIRANTIS = 'mirantis'
    NEBULA = 'nebula'
    OPENSTACK = 'openstack'
    OCS = 'ocs'
    RACKSPACENGUK = 'rackspacenguk'
    RACKSPACENGUS = 'rackspacengus'
    VIO = 'vio'
    VMWARE = 'vmware'


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
