import pytest

from revizor2.api import Farm
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus
from scalarizr.lib import farm as lib_farm
from scalarizr.lib import server as lib_server
from scalarizr.lifecycle.common import docker, lifecycle


class TestDocker:
    """Docker compatibility"""

    order = ('test_bootstrapping',
             'test_delete_containers',
             'test_stopresume_containers')

    @pytest.mark.run_only_if(platform=['ec2', 'gce'], dist=['!centos-6-x'])
    def test_bootstrapping(self, context: dict, cloud: Cloud, farm: Farm, servers: dict):
        """Bootstraping"""
        lib_farm.add_role_to_farm(context, farm)
        farm.launch()
        server = lib_server.wait_server_status(context, cloud, farm, status=ServerStatus.RUNNING)
        servers['M1'] = server
        docker_client = docker.install_docker(cloud, server)
        context['M1_docker_client'] = docker_client
        docker.start_containers(docker_client)
        docker.validate_containers(server, docker_client)

    @pytest.mark.run_only_if(platform=['ec2', 'gce'], dist=['!centos-6-x'])
    def test_delete_containers(self, context: dict, servers: dict):
        """Delete docker containers"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        docker_client = context['M1_docker_client']
        docker.modify_random_containers(docker_client, amount=10, action='delete')
        docker.validate_containers(server, docker_client)

    @pytest.mark.run_only_if(platform=['ec2', 'gce'], dist=['!centos-6-x'])
    def test_stopresume_containers(self, context: dict, servers: dict):
        """Stop/resume docker containers"""
        server = servers['M1']
        lifecycle.assert_server_status(server, ServerStatus.RUNNING)
        docker_client = context['M1_docker_client']
        stopped_containers = docker.modify_random_containers(docker_client, amount=10, action='stop')
        docker.validate_containers(server, docker_client)
        docker.start_stopped_containers(docker_client, stopped_containers)
        docker.validate_containers(server, docker_client)
