import re
import pika
import urllib2
import base64
import logging

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.consts import Platform


LOG = logging.getLogger(__name__)


@step('([\w]+) is (.+) node$')
def assert_check_node_type(step, serv_as, node_type):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    out = node.run('rabbitmqctl cluster_status')
    LOG.info('Rabbitmq serverer %s status: %s' % (server.id, out))
    disks = re.findall(r'disc,\[(.+)\]},', out[0])[0]
    disks = re.findall("'((?:[a-z0-9@-]+)\@(?:[a-z0-9@-]+))+'", disks)
    LOG.info('Rabbitmq serverer %s status disks: %s' % (server.id, disks))
    rams = re.findall(r"{ram,\[(.+)\]}]},", out[0])
    if rams:
        rams = re.findall(r"'((?:[a-z0-9@-]+)\@(?:[a-z0-9@-]+))+'", rams[0])
        LOG.info('Rabbitmq serverer %s status rams: %s' % (server.id, rams))
    if node_type == 'hdd':
        world.assert_not_in('rabbit@rabbit-%s' % server.index, disks, 'server %s is not %s node' % (server.id, node_type))
    elif node_type == 'ram':
        world.assert_not_in('rabbit@rabbit-%s' % server.index, rams, 'server %s is not %s node' % (server.id, node_type))


# @step('I (increase|decrease) minimum servers to (.+) for (.+) role$')
# def increase_instances(step, action_type, count, role_type):
#     role = world.get_role(role_type)
#     options = { "scaling.max_instances": int(count) + 1,
#                             "scaling.min_instances": count,
#                             "rabbitmq.nodes_ratio": "66%", }
#     LOG.info('Edit role options to: %s' % options)
#     world.farm.edit_role(role.role_id, options)


@step('I check (.+) nodes in cluster on ([\w]+)$')
def assert_node_count(step, node_count, serv_as):
    serv = getattr(world, serv_as)
    node = world.cloud.get_node(serv)
    out = node.run('rabbitmqctl cluster_status')
    co = len(re.findall(r'running_nodes,\[(.+)\]}', out[0])[0].split(','))
    LOG.info('Nodes in rabbitmq cluster: %s' % co)
    world.assert_not_equal(int(node_count), co, 'Node count is failure, in config %s, but must %s' % (co, node_count))


@step('([\w]+) nodes are hdd and (.+) node is ram on ([\w]+)$')
def assert_server_ratio(step, hdd_count, ram_count, serv_as):
    serv = getattr(world, serv_as)
    node = world.cloud.get_node(serv)
    out = node.run('rabbitmqctl cluster_status')
    disks = re.findall(r'disc,\[(.+)\]},', out[0])[0]
    disks = re.findall("'((?:[a-z0-9@-]+)\@(?:[a-z0-9@-]+))+'", disks)
    LOG.info('Disks nodes in rabbitmq cluster: %s' % disks)
    rams = re.findall(r"{ram,\[(.+)\]}]},", out[0])
    if not rams:
        raise AssertionError('RAM nodes in rabbitmq is unavailable. All nodes: %s' % out[0])
    rams = re.findall(r"'((?:[a-z0-9@-]+)\@(?:[a-z0-9@-]+))+'", rams[0])
    LOG.info('RAMs nodes in rabbitmq cluster: %s' % rams)
    runnings = re.findall(r'running_nodes,\[(.+)\]}', out[0])[0]
    runnings = re.findall("'((?:[a-z0-9@-]+)\@(?:[a-z0-9@-]+))+'", runnings)
    LOG.info('Running nodes in rabbitmq cluster: %s' % runnings)
    all_count = len(disks) + len(rams)
    world.assert_not_equal(all_count, len(runnings),
                                            "Count of runnings server in cluster is different, running %s in cluster but must: %s" % (len(runnings), all_count))
    world.assert_not_equal(int(hdd_count), len(disks),
                                            "Count of disk nodes is failure, disks %s must %s" % (len(disks), hdd_count))
    world.assert_not_equal(int(ram_count), int(ram_count),
                                            "Count of ram nodes is failure, disks %s must %s" % (len(rams), hdd_count))


@step('I add ([\w]+) to (.+)$')
def add_objects(step, obj, serv_as):
    """
    Insert data to RabbitMQ server
    """
    serv = getattr(world, serv_as)
    node = world.cloud.get_node(serv)
    password = wait_until(world.wait_rabbitmq_cp, timeout=360, error_text="Not see detail to rabbitmq panel")['password']
    setattr(world, 'rabbitmq_password', password)
    LOG.info('Rabbitmq password: %s' % password)
    port = 5672
    if CONF.feature.driver.current_cloud in [Platform.IDCF,
                                             Platform.CLOUDSTACK]:
        port = world.cloud.open_port(node, port)
    if obj == 'user':
        node.run('rabbitmqctl add_user testuser testpassword')
        LOG.info('Add user scalr to rabbitmq')
    elif obj == 'vhost':
        node.run('rabbitmqctl add_vhost testvhost')
        LOG.info('Add vhost "testvhost" to rabbitmq')
    elif obj == 'queue':
        credentials = pika.PlainCredentials('scalr', password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                                                                       host=str(serv.public_ip),
                                                                       port=int(port)))
        channel = connection.channel()
        channel.queue_declare(queue='test_queue', durable=True)
        LOG.info('Add queue "test_queue" to rabbitmq')
    elif obj == 'message':
        credentials = pika.PlainCredentials('scalr', password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                                                                       host=str(serv.public_ip),
                                                                       port=int(port)))
        channel = connection.channel()
        channel.basic_publish(exchange='', routing_key='test_queue', body='super test message',
                                                properties=pika.BasicProperties(delivery_mode=2,))
        LOG.info('Add message to rabbitmq')


@step('I enable control panel$')
def enable_cp(step):
    world.farm.rabbitmq_cp_enable()
    LOG.info('Enable rabbitmq control panel')


@step('control panel work$')
def check_cp(step):
    LOG.info('Check control panel work')
    detail = wait_until(world.wait_rabbitmq_cp_url, timeout=1000, error_text="Not see detail to rabbitmq panel")
    req = urllib2.Request(detail['url'].replace('\\', ''))
    code = base64.encodestring('%s:%s' % ('scalr', detail['password']))[:-1]
    req.add_header("Authorization", "Basic %s" % code)
    p = urllib2.urlopen(req)
    page = p.read()
    LOG.debug('Control panel page content: %s' % page)
    world.assert_not_in('RabbitMQ Management', page, 'Control panel not work')
    #if not 'RabbitMQ Management' in p.read():
    #       raise AssertionError('Control panel not work')


@step('([\w]+) exists in (.+)$')
def assert_check_objects(step, obj, serv_as):
    """
    Verify RabbitMQ object exists
    """
    serv = getattr(world, serv_as)
    node = world.cloud.get_node(serv)
    password = getattr(world, 'rabbitmq_password')
    port = 5672
    if CONF.feature.driver.current_cloud in [Platform.IDCF,
                                             Platform.CLOUDSTACK]:
        port = world.cloud.open_port(node, port)
    if obj == 'user':
        LOG.info('Check user in rabbitmq')
        out = node.run('rabbitmqctl list_users')[0]
        world.assert_not_in('scalr', out, 'Not user scalr in list_users: %s' % out)
        #if not 'scalr' in out[0]:
        #       raise AssertionError('Not user guest in list_users: %s' % out[0])
    elif obj == 'vhost':
        LOG.info('Check vhost in rabbitmq')
        out = node.run('rabbitmqctl list_vhosts')[0]
        world.assert_not_in('testvhost', out, 'Not vhost testvhost in list_vhosts: %s' % out)
        #if not 'testvhost' in out[0]:
        #       raise AssertionError('Not vhost testvhost in list_vhosts: %s' % out[0])
    elif obj == 'queue':
        LOG.info('Check queue in rabbitmq')
        out = node.run('rabbitmqctl list_queues')[0]
        world.assert_not_in('test_queue', out, 'Not queue test_queue in list_queues: %s' % out)
        #if not 'test_queue' in out[0]:
        #       raise AssertionError('Not queue test_queue in list_queues: %s' % out[0])
    elif obj == 'message':
        LOG.info('Check  message in rabbitmq')
        credentials = pika.PlainCredentials('scalr', password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials,
                                                                       host=str(serv.public_ip),
                                                                       port=int(port)))
        channel = connection.channel()
        try:
            m = channel.basic_get(queue='test_queue')
            LOG.info('Give message in queue "test_queue"')
            world.assert_not_equal(m[2], 'super test message', 'Message is not our, I\'m get: %s' % m[2])
            #if not m[2] == 'super test message':
            #       raise AssertionError('Message is not our, I\'m get: %s' % m)
        except pika.exceptions.AMQPChannelError:
            raise AssertionError('Queue is not work')
