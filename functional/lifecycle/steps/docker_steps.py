import logging
import docker
import random
import copy
import time
import string

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.fixtures import tables
from revizor2.api import CONF
from revizor2.backend import IMPL


LOG = logging.getLogger(__name__)

NON_ASCII_SCRIPT = u'\u0442\u0435\u0441\u0442.sh'.encode('utf-8')

NON_ASCII_COMMAND = u'bash /test/\u0442\u0435\u0441\u0442.sh'.encode('utf-8')


def get_server_containers(serv_as):
    server = getattr(world, serv_as)
    client = getattr(world, serv_as + '_client')
    containers = client.containers()
    server_containers = []
    for container in containers:
        printable = set(string.printable)
        container = {
            'command': filter(lambda x: x in printable, container['Command']),
            'containerId': container['Id'],
            'image': container['Image'],
            'labels': sorted([{
                'containerId': container['Id'],
                'name': l[0],
                'value': l[1]} for l in container['Labels'].items()]),
            'name': container['Names'][0],
            'network': container['HostConfig']['NetworkMode'],
            'ports': sorted([{
                'destination': str(p['PrivatePort']),
                'hostIp': p['IP'] if 'IP' in p else None,
                'protocol': p['Type'],
                'source': str(p['PublicPort']) if 'PublicPort' in p else None} for p in container['Ports']]),
            'privileged': client.inspect_container(container['Id'])['HostConfig']['Privileged'],
            'serverId': server.id,
            'volumes': sorted([{
                'containerId': container['Id'],
                'destination': filter(lambda x: x in printable, v['Destination']),
                'source': filter(lambda x: x in printable, v['Source'])} for v in container['Mounts']])}
        server_containers.append(container)
    return server_containers


@step('I install docker on (.+)$')
def install_docker(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    conf_folder = ''
    restart_cmd = 'service docker restart'
    if CONF.feature.dist in ['centos7', 'ubuntu1604', 'debian8', 'rhel7']:  # SystemD-based OS
        conf_file = '/etc/systemd/system/docker.service.d/docker.conf'
        echo_line = '''"[Service]\nExecStart=\nExecStart=/usr/bin/dockerd -H unix:///var/run/docker.sock -H tcp://0.0.0.0:9999"'''
        conf_folder = 'mkdir /etc/systemd/system/docker.service.d;'
        restart_cmd = 'systemctl daemon-reload; systemctl restart docker'
    else:
        conf_file = '/etc/default/docker'
        echo_line = """'DOCKER_OPTS="-H unix:///var/run/docker.sock -H tcp://0.0.0.0:9999"'"""
    command = '''curl -fsSL https://get.docker.com/ | sh; {}\
        echo -e {} >> {};\
        {}; \
        docker pull ubuntu; \
        docker pull nginx; \
        docker pull alpine'''.format(conf_folder, echo_line, conf_file, restart_cmd)
    node.run(command)
    node.run("iptables -I INPUT 1 -p tcp --dport 9999 -j ACCEPT")
    node.run('echo "sleep 1d" >> /home/scalr/{}'.format(NON_ASCII_SCRIPT))
    assert node.run('docker --version')
    client = docker.Client(base_url='http://%s:9999' % server.public_ip, version='auto')
    setattr(world, serv_as + '_client', client)


@step('I start docker containers on (.+)$')
def start_containers(step, serv_as):
    client = getattr(world, serv_as + '_client')
    configs = tables('docker').data
    images = ['ubuntu', 'alpine', 'nginx']
    ports_delta = 1
    for image in images:
        base_config = {
            "image": image,
            "command": "sleep 1d",
            "detach": True}
        for conf in configs:
            if conf.startswith('vol'):
                if conf == 'vol1' and image != 'alpine':
                    container = client.create_container(
                        host_config=client.create_host_config(binds=configs[conf]),
                        image=image, command=NON_ASCII_COMMAND, detach=True)
                else:
                    container = client.create_container(
                        host_config=client.create_host_config(binds=configs[conf]),
                        **base_config)

            elif conf.startswith('ports'):
                ports = {}
                for p in range(configs[conf]):
                    ports.update({9980 + ports_delta: 9980 + ports_delta})
                    ports.update({str(9981 + ports_delta) + '/udp': 9985 + ports_delta})
                    ports_delta += 1
                container = client.create_container(
                    host_config=client.create_host_config(port_bindings=ports),
                    ports=ports.keys(),
                    **base_config)

            elif conf.startswith('labels'):
                container = client.create_container(
                    labels=configs[conf],
                    **base_config)

            elif conf == 'privileged':
                container = client.create_container(
                    host_config=client.create_host_config(privileged=configs[conf]),
                    **base_config)
            else:
                entry_config = copy.copy(base_config)
                entry_config.pop('command')
                container = client.create_container(
                    entrypoint=configs[conf],
                    **entry_config)
            client.start(container)


@step('verify containers on Scalr and (.+) are identical')
def verify_containers(step, serv_as):
    server = getattr(world, serv_as)
    server_containers = get_server_containers(serv_as)

    start_time = time.time()
    while time.time() < (start_time + 300):
        scalr_containers = wait_until(
            IMPL.containers.list,
            args={'server_id': server.id},
            timeout=120,
            logger=LOG,
            error_text="No docker containers were found on Scalr for server %s" % server.id)
        if len(server_containers) == len(scalr_containers):
            break
        else:
            time.sleep(10)

    for serv_container in server_containers:
        for scalr_container in scalr_containers:
            if serv_container['containerId'] == scalr_container['containerId']:
                assert serv_container == scalr_container,\
                    "Containers don't match! Server: \n{}\nScalr: \n{}".format(serv_container, scalr_container)


@step('I (delete|stop) (\d+) of the running containers on (.+)$')
def modify_random_containers(step, action, amount, serv_as):
    client = getattr(world, serv_as + '_client')
    server_containers = client.containers()
    stopped_containers = []
    for _ in range(int(amount)):
        container = random.choice(server_containers)
        if action == 'delete':
            client.remove_container(container, force=True)
            server_containers.remove(container)
        elif action == 'stop':
            client.stop(container)
            stopped_containers.append(container)
    setattr(world, 'stopped_containers', stopped_containers)


@step('I start stopped containers on (.+)$')
def start_stopped_containers(step, serv_as):
    client = getattr(world, serv_as + '_client')
    for container in getattr(world, 'stopped_containers'):
        client.start(container)
