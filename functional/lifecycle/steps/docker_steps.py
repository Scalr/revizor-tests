import logging
import docker
import random
import copy

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.fixtures import tables
from revizor2.api import CONF, Dist


LOG = logging.getLogger(__name__)


@step('I install docker on (.+)$')
def install_docker(step, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    conf_folder = ''
    restart_cmd = 'sudo service docker restart'
    if CONF.feature.dist in ['centos7', 'ubuntu1604', 'debian8', 'rhel7']:
        conf_file = '/etc/systemd/system/docker.service.d/docker.conf'
        echo_line = '''"[Service]\nExecStart=\nExecStart=/usr/bin/dockerd -H unix:///var/run/docker.sock -H tcp://0.0.0.0:9999"'''
        conf_folder = 'sudo mkdir /etc/systemd/system/docker.service.d;'
        restart_cmd = 'sudo systemctl daemon-reload; sudo systemctl restart docker'
    else:
        conf_file = '/etc/default/docker'
        echo_line = 'DOCKER_OPTS="-H unix:///var/run/docker.sock -H tcp://0.0.0.0:9999"'
    command = '''curl -fsSL https://get.docker.com/ | sh; {}\
        echo -e {} >> {};\
        {}; \
        docker pull ubuntu; \
        docker pull nginx; \
        docker pull alpine'''.format(conf_folder, echo_line, conf_file, restart_cmd)
    node.run(command)
    assert node.run('docker --version')


@step('I start docker containers on (.+)$')
def start_containers(step, serv_as):
    server = getattr(world, serv_as)
    client = docker.Client(base_url='http://%s:9999' % server.public_ip, version='auto')
    configs = tables('docker').data
    images = ['ubuntu', 'alpine', 'nginx']
    ports_delta = 1
    for image in images:
        # client.get_image(image)
        base_config = {
            "image": image,
            "command": "sleep 1d",
            "detach": True}
        for conf in configs:
            if conf.startswith('vol'):
                container = client.create_container(
                    host_config=client.create_host_config(binds=configs[conf]),
                    **base_config)

            elif conf.startswith('ports'):
                ports = {}
                for p in range(configs[conf]):
                    ports.update({9980 + ports_delta: 9980 + ports_delta})
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
    scalr_containers = wait_until(server.get_containers,
        timeout=120,
        logger=LOG,
        error_text="No docker containers were found on Scalr for server %s" % server.id)['containers']
    client = docker.Client(base_url='http://%s:9999' % server.public_ip, version='auto')
    server_containers = client.containers()
    scalr_container_ids = []
    for scalr_container in scalr_containers:
        scalr_container_ids.append(scalr_container['containerId'])
    for server_container in server_containers:
        for scalr_container in scalr_containers:
            if server_container['Id'] == scalr_container['containerId']:
                # Assert volume mounts
                server_volumes = []
                for serv_vol in server_container['Mounts']:
                    server_volumes.append({
                        'destination': serv_vol['Destination'],
                        'source': serv_vol['Source']})
                scalr_volumes = []
                for scalr_vol in scalr_container['volumes']:
                    scalr_vol.pop('containerId')
                    scalr_volumes.append(scalr_vol)
                assert not any(volume not in scalr_volumes for volume in server_volumes), "Volumes for container %s are incorrect.\
                    \nScalr:\n%s\nInstance:\n%s" % (server_container['Id'], scalr_volumes, server_volumes)

                # Assert ports
                server_ports = []
                for serv_port in server_container['Ports']:
                    port = {
                        'destination': str(serv_port['PrivatePort']),
                        'protocol': serv_port['Type'],
                        'source': str(serv_port['PublicPort']) if 'PublicPort' in serv_port.keys() else None,
                        'hostIp': serv_port['IP'] if 'IP' in serv_port.keys() else None}
                    server_ports.append(port)
                scalr_ports = []
                for scalr_port in scalr_container['ports']:
                    scalr_port.pop('containerId')
                    scalr_port.pop('uuid')
                    scalr_ports.append(scalr_port)
                assert not any(port not in scalr_ports for port in server_ports), "Ports for container %s are incorrect.\
                    \nScalr:\n%s\nInstance:\n%s" % (server_container['Id'], scalr_ports, server_ports)

                # Assert labels
                scalr_labels = {}
                for label in scalr_container['labels']:
                    scalr_labels[label['name']] = ''
                assert scalr_labels == server_container['Labels'], "Labels for container %s are incorrect.\
                    \nScalr:\n%s\nInstance:\n%s" % (server_container['Id'], scalr_labels, server_container['Labels'])

                # Assert privileged status
                assert scalr_container['privileged'] == client.inspect_container(server_container['Id'])['HostConfig']['Privileged']

                # Assert entrypoint and no command
                if not client.inspect_container(server_container['Id'])['Config']['Cmd']:
                    assert scalr_container['command'].split(' ') == client.inspect_container(server_container['Id'])['Config']['Entrypoint']


@step('I (delete|stop) (\d+) of the running containers on (.+)$')
def modify_random_containers(step, action, amount, serv_as):
    server = getattr(world, serv_as)
    client = docker.Client(base_url='http://%s:9999' % server.public_ip, version='auto')
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
    server = getattr(world, serv_as)
    client = docker.Client(base_url='http://%s:9999' % server.public_ip, version='auto')
    for container in getattr(world, 'stopped_containers'):
        client.start(container)
