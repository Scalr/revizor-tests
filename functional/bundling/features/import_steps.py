import os
import time
from datetime import datetime
import logging
import json

from lettuce import world, step, after

from revizor2.conf import CONF
from revizor2.api import Farm, IMPL, Server
from revizor2.consts import ServerStatus, OS, Platform
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.fixtures import tables

LOG = logging.getLogger('import')

#User data fixtures
#ec2 - (ec2, eucalyptus),  gce-gce, openstack-(openstack, ecs, rackspaceng), cloudstack-(cloudstack, idcf, ucloud)
USER_DATA = {
                "ec2": {
                    "behaviors": "base,chef",
                    "farmid": "16674",
                    "message_format": "json",
                    "owner_email": "stunko@scalr.com",
                    "szr_key": "9gRW4akJmHYvh6W3vd6GzxOPtk/iQHL+8aZRZZ1u",
                    "s3bucket": "",
                    "cloud_server_id": "",
                    "env_id": "3414",
                    "server_index": "1",
                    "platform": "ec2",
                    "role": "base,chef",
                    "hash": "e6f1bfd5bbf612",
                    "custom.scm_branch": "master",
                    "roleid": "36318",
                    "farm_roleid": "60818",
                    "serverid": "96e52104-f5c4-4ce7-a018-c8c2eb571c99",
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "us-east-1",
                    "httpproto": "https",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "cloud_storage_path": "s3://"
                },

                "gce": {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "app",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60832",
                    "message_format": "json",
                    "realrolename": "apache-ubuntu1204-devel",
                    "region": "x-scalr-custom",
                    "httpproto": "https",
                    "szr_key": "NiR2xOZKVbvdMPgdxuayLjEK2xC7mtLkVTc0vpka",
                    "platform": "gce",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "app",
                    "cloud_server_id": "",
                    "roleid": "36319",
                    "env_id": "3414",
                    "serverid": "c2bc7273-6618-4702-9ea1-f290dca3b098",
                    "cloud_storage_path": "gcs://",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                },

                "openstack": {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "base,chef",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60821",
                    "message_format": "json",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "ItalyMilano1",
                    "httpproto": "https",
                    "szr_key": "iyLO/+iOGFFcuSIxbr0IJteRwDjaP1t6NQ8kXbX6",
                    "platform": "ecs",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "base,chef",
                    "roleid": "36318",
                    "env_id": "3414",
                    "serverid": "59ddbdbf-6d69-4c53-a6b7-76ab391a8465",
                    "cloud_storage_path": "swift://",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                },

                "cloudstack": {
                    "p2p_producer_endpoint": "https://my.scalr.com/messaging",
                    "behaviors": "base,chef",
                    "owner_email": "stunko@scalr.com",
                    "hash": "e6f1bfd5bbf612",
                    "farmid": "16674",
                    "farm_roleid": "60826",
                    "message_format": "json",
                    "realrolename": "base-ubuntu1204-devel",
                    "region": "jp-east-f2v",
                    "httpproto": "https",
                    "szr_key": "cg3uuixg4jTUDz/CexsKpoNn0VZ9u6EluwpV+Mgi",
                    "platform": "idcf",
                    "queryenv_url": "https://my.scalr.com/query-env",
                    "role": "base,chef",
                    "cloud_server_id": "",
                    "roleid": "36318",
                    "env_id": "3414",
                    "serverid": "feab131b-711e-4f4a-a7dc-ba083c28e5fc",
                    "custom.scm_branch": "master",
                    "server_index": "1"
                }
}


@step('I have a server([\w ]+)? running in cloud$')
def given_server_in_cloud(step, user_data):
    #TODO: Add install behaviors
    LOG.info('Create node %s in cloud' % user_data)
    #Convert dict to formatted str
    dict_to_str = lambda d: ';'.join(['='.join([key, value]) if value else key for key, value in d.iteritems()])
    #Get user data fixture for tested Cloud
    user_data = dict_to_str(USER_DATA[Platform.get_platform_group(CONF.main.driver)]) if user_data \
        else None
    #Create node
    node = world.cloud.create_node(userdata=user_data)
    #Install scalarizr to server
    LOG.info('Install scalarizr in node')
    node.install_scalarizr(branch=CONF.main.branch)
    setattr(world, 'cloud_server', node)
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        #Get node external ip
        #Run command
        out = node.run('wget -qO- ifconfig.me/ip')
        if not out[1]:
            ip_address = out[0].rstrip("\n")
            LOG.info('Received external ip address of the node. IP:%s' % ip_address)
            setattr(world, 'ip', ip_address)
        else:
            raise AssertionError("Can't get node external ip address. Original error: %s" % out[1])
        #Open port, set firewall rule
        new_port = world.cloud.open_port(node, 8013, ip=ip_address)
        setattr(world, 'forwarded_port', new_port)
        if not new_port == 8013:
            raise AssertionError('Import will failed, because opened port is not 8013, '
                                 'an installed port is: %s' % new_port)


@step('I trigger the Start building and run scalarizr')
def start_building(step):
    time.sleep(180)
    LOG.info('Initiate Start building')

    #Emulation pressing the 'Start building' key on the form 'Create role from
    #Get CloudServerId, Command to run scalarizr
    if CONF.main.driver == Platform.GCE:
        server_id = world.cloud_server.name
    else:
        server_id = world.cloud_server.id
    res = IMPL.bundle.import_start(platform=CONF.main.platform,
                                   location=CONF.platforms[CONF.main.platform]['location'],
                                   cloud_id=server_id,
                                   name='test-import-%s' % datetime.now().strftime('%m%d-%H%M'))
    if not res:
        raise AssertionError("The import process was not started. Scalarizr run command was not received.")
    LOG.info('Start scalarizr on remote host. ServerId is: %s' % res['server_id'])
    LOG.info('Scalarizr run command is: %s' % res['scalarizr_run_command'])
    world.server = Server(**{'id': res['server_id']})

    #Run screen om remote host in "detached" mode (-d -m This creates a new session but doesn't  attach  to  it)
    #and then run scalarizr on new screen
    world.cloud_server.run('screen -d -m %s &' % res['scalarizr_run_command'])


@step('Connection with scalarizr was established')
def is_scalarizr_connected(step, timeout=1400):
    LOG.info('Establish connection with scalarizr.')
    #Whait outbound request from scalarizr
    res = wait_until(IMPL.bundle.check_scalarizr_connection, args=(world.server.id, ), timeout=timeout,
                     error_text="Time out error. Can't establish connection with scalarizr.")
    if not res['failure_reason']:
        world.bundle_task_id = res['bundle_task_id']
        if not res['behaviors']:
            world.behaviors = ['base']
        elif 'base' not in res['behaviors']:
            world.behaviors = ','.join((','.join(res['behaviors']), 'base')).split(',')
        else:
            world.behaviors = res['behaviors']
        LOG.info('Connection with scalarizr was established.')
    else:
        raise AssertionError("Can't establish connection with scalarizr. Original error: %s" % res['failure_reason'])


@step('I trigger the Create role')
def create_role(step):
    behaviors_name = CONF.main.behaviors
    LOG.info('Create new role with %s behaviors.' % ','.join(behaviors_name))
    for behavior in behaviors_name:
        if not behavior in world.behaviors:
            raise AssertionError('Transmitted behavior: %s, not in the list received from the server' % behavior)

    res = IMPL.bundle.create_role(server_id=world.server.id,
                                  bundle_task_id=world.bundle_task_id,
                                  behaviors=','.join(behaviors_name))
    if not res:
        raise AssertionError('Create role initialization is failed.')


@step('Role has successfully been created$')
def assert_role_task_created(step,  timeout=1400):
    res = wait_until(IMPL.bundle.assert_role_task_created, args=(world.bundle_task_id, ), timeout=timeout,
                     error_text="Time out error. Can't create role with sent behaviors: $s." % CONF.main.behaviors)
    if res['failure_reason']:
        raise AssertionError("Can't create role. Original error: %s" % res['failure_reason'])
    LOG.info('New role was created successfully with Role_id: %s.' % res['role_id'])
    world.new_role_id = res['role_id']
    #Remove port forward rule for Cloudstack
    if CONF.main.driver in [Platform.CLOUDSTACK, Platform.IDCF, Platform.KTUCLOUD]:
        LOG.info('Deleting a Port Forwarding Rule. IP:%s, Port:%s' % (world.forwarded_port, world.ip))
        if not world.cloud.close_port(world.cloud_server, world.forwarded_port, ip=world.ip):
            raise AssertionError("Can't delete a port forwarding Rule.")
        LOG.info('Port Forwarding Rule was successfully removed.')
    #Destroy virtual machine in Cloud
    LOG.info('Destroying virtual machine %s in Cloud' % world.cloud_server.id)
    if not world.cloud_server.destroy():
        raise AssertionError("Can't destroy node with id: %s." % world.cloud_server.id)
    LOG.info('Virtual machine was successfully destroyed.')


@step('I add to farm imported role$')
def add_new_role_to_farm(step):
    world.farm.add_role(world.new_role_id)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, 'role_type', ','.join(role.role.behaviors))
    setattr(world, '%s_role' % ','.join(role.role.behaviors), role)
