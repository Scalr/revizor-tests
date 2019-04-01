import logging
import typing as tp

from libcloud.compute.base import NodeImage

from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.fixtures import tables
from revizor2.consts import Platform
from revizor2.cloud.node import ExtendedNode

LOG = logging.getLogger(__name__)

USER_DATA = {
    Platform.EC2: {
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

    Platform.GCE: {
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

    Platform.OPENSTACK: {
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

    Platform.CLOUDSTACK: {
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


def run_server_in_cloud(cloud: Cloud, user_data: bool = False) -> ExtendedNode:
    LOG.info(f'Create node in cloud. User_data: {user_data}')
    # Convert dict to formatted str
    platform = CONF.feature.platform
    if user_data:
        dict_to_str = lambda d: ';'.join(['='.join([key, value]) if value else key for key, value in d.iteritems()])
        user_data = dict_to_str(USER_DATA[platform.cloud_family])
        if platform.is_gce:
            user_data = {'scalr': user_data}
    else:
        user_data = None
    # Create node
    image = None
    if CONF.feature.dist.is_windows or CONF.feature.dist.id == 'coreos':
        table = tables('images-clean')
        search_cond = dict(
            dist=CONF.feature.dist.id,
            platform=platform.name)
        image = table.filter(search_cond).first().keys()[0].encode('ascii', 'ignore')
    node = cloud.create_node(userdata=user_data, image=image)
    LOG.info(f'Cloud server successfully created with name: "{node.name}"')
    # if platform.is_cloudstack:
    #     # Run command
    #     out = node.run('wget -qO- ifconfig.me/ip')
    #     if not out.std_err:
    #         ip_address = out[0].rstrip("\n")
    #         LOG.info('Received external ip address of the node. IP:%s' % ip_address)
    #         setattr(world, 'ip', ip_address)
    #     else:
    #         raise AssertionError("Can't get node external ip address. Original error: %s" % out.std_err)
    #     # Open port, set firewall rule
    #     new_port = world.cloud.open_port(node, 8013, ip=ip_address)
    #     setattr(world, 'forwarded_port', new_port)
    #     if not new_port == 8013:
    #         raise AssertionError('Import will failed, because opened port is not 8013, '
    #                              'an installed port is: %s' % new_port)
    return node


def get_node_image(node: ExtendedNode) -> NodeImage:
    # Moved to discovery.py
    image = None
    if node.platform_config.is_gce:
        image = node.driver.ex_get_image(node.extra['image'])
    elif node.platform_config.is_ec2:
        image = node.driver.get_image(node.extra['image_id'])
    elif node.platform_config.is_azure:
        image = node.cloud.find_image()
    LOG.debug(f'Obtained image ({image.name} - {image.id}) from cloud instance {node.id}')
    assert image, f'Image from node {node.id} not created!'
    return image
