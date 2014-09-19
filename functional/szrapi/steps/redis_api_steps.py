# coding: utf-8

"""
Created on 09.19.2014
@author: Eugeny Kurkovich
"""

import logging
from lettuce import step, world

LOG = logging.getLogger('Redis api steps')


def get_api_command_result(command):

 # Get api command result
    api_result = getattr(world, ''.join((command, '_res')))
    LOG.debug('Obtained api command {0} result: {1}'.format(
        command,
        api_result))
    return api_result


@step(r'number of redis instance is ([\d]+)')
def check_redis_instances_count(step, instances_count):
    api_result = get_api_command_result('list_processes')
    try:
        assertion_data = len(api_result.get('ports', []))
        assert (assertion_data == int(instances_count))
        LOG.debug('Number of running processes: ({0}), and expected:({1}) the same.'.format(
            assertion_data,
            instances_count
        ))
    except AssertionError:
        raise AssertionError('Number of running processes: ({0}), and expected:({1}) is not equal.'.format(
            assertion_data,
            instances_count
        ))


@step(r'redis instance ports is ([\d\,]+)')
def check_redis_instances_ports(step, instances_ports):
    api_result = get_api_command_result('list_processes')
    try:
        tested_instances_ports = [int(port.strip()) for port in instances_ports.split(',')]
        running_instances_ports = api_result.get('ports', [])
        assert all(port in tested_instances_ports for port in running_instances_ports)
        LOG.debug('Running redis processes: {0} listening to specific ports: {1}'.format(
            running_instances_ports,
            tested_instances_ports
        ))
    except AssertionError:
        raise AssertionError('Running redis processes: {0} listening to not specific ports: {1}'.format(
            running_instances_ports,
            tested_instances_ports
        ))


@step(r'([\d\,]+) redis instance is running')
def check_redis_instances_state(step, instances_ports):
    redis_processes_states = get_api_command_result('get_service_status')
    try:
        tested_redis_processes = instances_ports.split(',')
        assert all(redis_processes_states[port] == 0 for port in tested_redis_processes)
        LOG.debug('All redis processes: {0} is running'.format(tested_redis_processes))
    except AssertionError:
        raise AssertionError('Not all processes have the status: running - (0): {} .'.format(redis_processes_states))

"""
    server = getattr(world, serv_as)
    # Get service api
    api = getattr(getattr(szrapi, service_api)(server), command)
    LOG.debug('Set %s instance %s for server %s' % (service_api, api, server.id))

    scalarizr_key = server.details.get('scalarizr.key')
    api = SzrApiServiceProxy(server.public_ip, scalarizr_key)

    answer = api.redis.list_processes()

    LOG.debug('API response from list_processes: %s' % answer)

    if not len(answer['ports']) == int(instances_count):
        raise AssertionError('Invalid redis processes count via API, must be: %s but get answer %s' %
                             (instances_count, answer))

@step('I add ([\d]+) redis ([\w]+) instance to ([\w]+)$')
def upscale_redis_instances(step, instances_count, instance_type, serv_as):
    server = getattr(world, serv_as)
    scalarizr_key = server.details.get('scalarizr.key')
    api = SzrApiServiceProxy(server.public_ip, scalarizr_key)
    key = open('/tmp/%s_apikey' % server.id, 'w+')
    key.write(scalarizr_key)
    key.close()
    LOG.info('Write key file from server %s to file %s' % (server.id, key.name))
    ports = getattr(world, 'redis_instances', {})
    if instance_type == 'master':
        LOG.info('Run %s master instances' % instances_count)
        answer = api.redis.launch_processes(num=int(instances_count))
        LOG.debug('API response: %s' % answer)
        ports.update(zip(answer['ports'], answer['passwords']))
        setattr(world, 'redis_instances', ports)
    elif instance_type == 'slave':
        answer = api.redis.launch_processes(num=int(instances_count),
                                            ports=ports.keys()[1:int(instances_count)+1],
                                            passwords=ports.values()[1:int(instances_count)+1]
                                            )
        LOG.debug('API response: %s' % answer)
    if not len(answer['ports']) == int(instances_count):
        raise AssertionError('Count of running instances %s, but must be: %s' % (len(answer['ports']), instances_count))


@step('([\d]+) redis instances work in ([\w]+)$')
def check_redis_instances(step, instances_count, serv_as):
    server = getattr(world, serv_as)
    instances = getattr(world, 'redis_instances', {})
    count = 0
    LOG.info('Check working redis ports')
    #TODO: Rewrite this
    for instance in instances:
        if CONF.feature.platform in ['cloudstack', 'idcf']:
            cloud = Cloud()
            node = cloud.get_node(server)
            ip = filter(lambda x: x.address == server.public_ip, node.driver.ex_list_public_ip())[0]
            try:
                rule = node.driver.ex_add_port_forwarding_rule(node, ip, 'TCP', instance, instance)
            except:
                rules = node.driver.ex_list_port_forwarding_rule()
                rule = filter(lambda x: x.public_port == instance and x.address == ip, rules)[0]
            LOG.info('Rule for open port add: %s %s - %s' % (ip, instance, instance))
        try:
            LOG.debug('Try connect to redis instance: %s:%s:%s' % (server.public_ip, instance, instances[instance]))
            r = redis.Redis(host=server.public_ip, port=instance, password=instances[instance], socket_timeout=5)
            r.ping()
            count += 1
        except redis.ConnectionError, e:
            LOG.error('Connection to redis: %s:%s with password %s is FAILED' % (server.public_ip, instance,
                                                                               instances[instance]))
            raise redis.ConnectionError('Connection to redis: %s:%s with password %s is FAILED' % (server.public_ip, instance,
                                                                                                   instances[instance]))
        finally:
            if CONF.feature.platform in ['cloudstack', 'idcf']:
                node.driver.ex_delete_port_forwarding_rule(node, rule)
                LOG.info('Rule for open port was delete')
    if not count == int(instances_count):
        LOG.error('Working instance count is %s, but must %s' % (count, instances_count))


@step('([\d]+) redis instances is ([\w]+) in ([\w]+)$')
def check_redis_instances(step, instances_count, instance_type, serv_as):
    server = getattr(world, serv_as)
    instances = getattr(world, 'redis_instances', {})
    count = 0
    for instance in instances:
        if CONF.feature.platform in ['cloudstack', 'idcf']:
            cloud = Cloud()
            node = cloud.get_node(server)
            ip = filter(lambda x: x.address == server.public_ip, node.driver.ex_list_public_ip())[0]
            try:
                rule = node.driver.ex_add_port_forwarding_rule(node, ip, 'TCP', instance, instance)
            except:
                rules = node.driver.ex_list_port_forwarding_rule()
                rule = filter(lambda x: x.public_port == instance and x.address == ip, rules)[0]
            LOG.info('Rule for open port add: %s %s - %s' % (ip, instance, instance))
        info = {}
        try:
            LOG.debug('Try connect to redis instance: %s:%s:%s' % (server.public_ip, instance, instances[instance]))
            r = redis.Redis(host=server.public_ip, port=instance, password=instances[instance], socket_timeout=5)
            info = r.info()
        except redis.ConnectionError, e:
            LOG.error('Connection to redis: %s:%s with password %s is FAILED' % (server.public_ip, instance,
                                                                                 instances[instance]))
            raise redis.ConnectionError('Connection to redis: %s:%s with password %s is FAILED' % (server.public_ip, instance,
                                                                                                   instances[instance]))
        finally:
            if CONF.feature.platform in ['cloudstack', 'idcf']:
                node.driver.ex_delete_port_forwarding_rule(node, rule)
                LOG.info('Rule for open port was delete')
        if info['role'] == instance_type:
            count += 1
        else:
            LOG.error('Redis instance: %s:%s is not %s' % (server.public_ip, instance, instance_type))
            raise AssertionError('Redis instance: %s:%s is not %s' % (server.public_ip, instance, instance_type))
    if not count == int(instances_count):
        LOG.error('%s instance count is %s, but must %s' % (instance_type, count, instances_count))


@step('I ([\w]+) data (?:to|from) redis ([\d]+) in ([\w]+)')
def action_on_redis(step, action, instance_number, serv_as):
    server = getattr(world, serv_as)
    instances = getattr(world, 'redis_instances', {})
    instance = sorted(instances.items())[int(instance_number)-1]
    if CONF.feature.platform in ['cloudstack', 'idcf']:
        cloud = Cloud()
        node = cloud.get_node(server)
        ip = filter(lambda x: x.address == server.public_ip, node.driver.ex_list_public_ip())[0]
        try:
            rule = node.driver.ex_add_port_forwarding_rule(node, ip, 'TCP', instance[0], instance[0])
        except:
            rules = node.driver.ex_list_port_forwarding_rule()
            rule = filter(lambda x: x.public_port == instance[0] and x.address == ip, rules)[0]
        LOG.info('Rule for open port add: %s %s - %s' % (ip, instance[0], instance[0]))
    r = redis.Redis(host=server.public_ip, port=instance[0], password=instance[1], socket_timeout=5, db=0)
    if action == 'write':
        LOG.info('Insert test key to %s:%s' % (server.public_ip, instance[0]))
        r.set('test_key', 'test_value')
    elif action == 'read':
        LOG.info('Read test key from %s:%s' % (server.public_ip, instance[0]))
        data = r.get('test_key')
        if not data == 'test_value':
            LOG.error('Receive bad key value from redis instance: %s:%s' % (server.public_ip, instance[0]))
            raise AssertionError('Receive bad key value from redis instance: %s:%s' % (server.public_ip, instance[0]))
    if CONF.feature.platform in ['cloudstack', 'idcf']:
        node.driver.ex_delete_port_forwarding_rule(node, rule)
        LOG.info('Rule for open port was delete')


@step('I delete ([\d]+) redis instance in ([\w]+)')
def delete_redis_instance(step, instances_count, serv_as):
    server = getattr(world, serv_as)
    instances = getattr(world, 'redis_instances', {})
    ports = sorted(instances.keys())[:int(instances_count)]
    LOG.debug('Delete %s redis instances from %s' % (instances_count, server.id))
    for port in ports:
        del(instances[port])
    key = open('/tmp/%s_apikey' % server.id, 'w+')
    scalarizr_key = server.details.get('scalarizr.key')
    key.write(scalarizr_key)
    key.close()
    api = SzrApiServiceProxy(server.public_ip, scalarizr_key)
    answer = api.redis.shutdown_processes(ports=ports, remove_data=True)
    LOG.debug('API response: %s' % answer)
    if not len(answer['ports']) == int(instances_count):
        raise AssertionError('Count of deleted instances %s, but must be: %s' % (len(answer['ports']),
                                                                                 instances_count))



@step('And redis not started in ([\w]+) port ([\d]+)')
def check_busy_port(step, serv_as, port):
    server = getattr(world, serv_as)
    scalarizr_key = server.details.get('scalarizr.key')
    api = SzrApiServiceProxy(server.public_ip, scalarizr_key)
    try:
        answer = api.redis.launch_processes(num=1, ports=[port,])
    except ServiceError, e:
        if 'Cannot launch Redis process on port %s: Already running' % port in e:
            return
        else:
            raise AssertionError('Not standart api error message: "%s"' % e)
"""