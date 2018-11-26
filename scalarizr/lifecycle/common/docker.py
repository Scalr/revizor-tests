import copy
import logging
import random
import string
import time
import typing as tp

import docker

from revizor2.api import Server
from revizor2.backend import IMPL
from revizor2.cloud import Cloud
from revizor2.conf import CONF
from revizor2.fixtures import tables
from revizor2.utils import wait_until

LOG = logging.getLogger(__name__)
# NOTE: PP > non-ascii test disabled until SCALRCORE-8645 is resolved
# NON_ASCII_SCRIPT = 'тест.sh'
# NON_ASCII_COMMAND = 'bash /test/тест.sh'
SCRIPT = 'test.sh'
COMMAND = 'bash /test/test.sh'


def filter_printable(text: str) -> str:
    """Removes character from string other than printable
    (digits + ascii_letters + punctuation + whitespace)
    """
    return ''.join(char for char in text if char in string.printable)


def get_server_containers(server: Server, client: docker.APIClient) -> tp.List[dict]:
    containers = client.containers()
    server_containers = []
    for container in containers:
        container = {
            'command': filter_printable(container['Command']),
            'containerId': container['Id'],
            'image': container['Image'],
            'labels': sorted([{
                'containerId': container['Id'],
                'name': l[0],
                'value': l[1]} for l in container['Labels'].items()],
                key=lambda label: label['name']),
            'name': container['Names'][0],
            'network': container['HostConfig']['NetworkMode'],
            'ports': sorted([{
                'destination': str(p['PrivatePort']),
                'hostIp': p['IP'] if 'IP' in p else None,
                'protocol': p['Type'],
                'source': str(p['PublicPort']) if 'PublicPort' in p else None} for p in container['Ports']],
                key=lambda port: (str(port['destination']), str(port['source']))),
            'privileged': client.inspect_container(container['Id'])['HostConfig']['Privileged'],
            'serverId': server.id,
            'volumes': sorted([{
                'containerId': container['Id'],
                'destination': filter_printable(v['Destination']),
                'source': filter_printable(v['Source'])} for v in container['Mounts']],
                key=lambda volume: volume['destination'])
        }
        server_containers.append(container)
    return server_containers


def install_docker(cloud: Cloud, server: Server) -> docker.APIClient:
    node = cloud.get_node(server)
    conf_folder = ''
    restart_cmd = 'service docker restart'
    if CONF.feature.dist.is_systemd:
        conf_file = '/etc/systemd/system/docker.service.d/docker.conf'
        echo_line = '''"[Service]\nExecStart=\nExecStart=/usr/bin/dockerd -H unix:///var/run/docker.sock -H tcp://0.0.0.0:3389"'''
        conf_folder = 'mkdir /etc/systemd/system/docker.service.d;'
        restart_cmd = 'systemctl daemon-reload; systemctl restart docker'
    else:
        conf_file = '/etc/default/docker'
        echo_line = """'DOCKER_OPTS="-H unix:///var/run/docker.sock -H tcp://0.0.0.0:3389"'"""
    command = '''curl -fsSL https://get.docker.com/ | sh; {}\
        echo -e {} >> {};\
        {}; \
        docker pull ubuntu; \
        docker pull nginx; \
        docker pull alpine'''.format(conf_folder, echo_line, conf_file, restart_cmd)
    with node.remote_connection() as conn:
        conn.run(command)
        conn.run("iptables -I INPUT 1 -p tcp --dport 3389 -j ACCEPT")
        conn.run('echo "sleep 1d" >> /home/scalr/{}'.format(SCRIPT))
        assert conn.run('docker --version')
    return docker.APIClient(base_url='http://%s:3389' % server.public_ip, version='auto')


def start_containers(client: docker.APIClient):
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
                        image=image, command=COMMAND, detach=True)
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
                    ports=[*ports],
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


def modify_random_containers(client: docker.APIClient, amount: int, action: str = 'stop') -> tp.List[dict]:
    server_containers = client.containers()
    stopped_containers = []
    for _ in range(amount):
        container = random.choice(server_containers)
        if action == 'delete':
            client.remove_container(container, force=True)
        elif action == 'stop':
            client.stop(container)
            stopped_containers.append(container)
        server_containers.remove(container)
    return stopped_containers


def start_stopped_containers(client: docker.APIClient, stopped_containers: list):
    for container in stopped_containers:
        client.start(container)


def validate_containers(server: Server, client: docker.APIClient):
    server_containers = get_server_containers(server, client)
    scalr_containers = []
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
                assert serv_container == scalr_container, \
                    "Containers don't match! Server: \n{}\nScalr: \n{}".format(serv_container, scalr_container)
