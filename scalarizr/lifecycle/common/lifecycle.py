import json
import logging
import re
import time
import typing as tp
from itertools import chain
from pathlib import Path

import scalarizr.lib.agent as lib_agent
import scalarizr.lib.role as lib_role
import scalarizr.lib.server as lib_server
from revizor2 import CONF
from revizor2.api import Server, Farm
from revizor2.backend import IMPL
from revizor2.cloud import Cloud
from revizor2.consts import ServerStatus, Platform
from revizor2.fixtures import resources
from revizor2.utils import wait_until
from scalarizr.lib.common import run_only_if

LOG = logging.getLogger(__name__)


def validate_server_status(server: Server, status: str):
    expected_status = ServerStatus.from_code(status)
    assert server.status == expected_status, \
        f'Server {server.id}: invalid status. ' \
        f'Actual: {server.status}, expected: {expected_status}'


@run_only_if(platform='!%s' % Platform.VMWARE)
def validate_vcpus_info(server: Server):
    vcpus = int(server.details['info.instance_vcpus'])
    LOG.info(f'Server {server.id} vcpus info: {vcpus}')
    assert vcpus > 0, f'info.instance_vcpus not valid for {server.id}'


def validate_scalarizr_version(server: Server, branch: str = None):
    if branch == 'system' or not branch:
        branch = CONF.feature.branch
    elif branch == 'role':
        branch = CONF.feature.to_branch
    LOG.info(f'Check scalarizr version is last in server {server.id} from branch {branch}')
    last_version = lib_agent.get_last_version(server.role.dist, branch)
    installed_version = lib_agent.get_installed_version(server)
    LOG.debug(f'Installed szr: {installed_version} last version: {last_version}')
    assert installed_version == last_version, \
        'Server does not have latest build of scalarizr package. ' \
        f'Actual: {installed_version}, expected: {last_version}'


def validate_hostname(server: Server):
    hostname = server.api.system.get_hostname().lower()
    valid_hostname = lib_server.get_hostname_by_server_format(server).lower()
    assert hostname == valid_hostname, \
        f'Hostname of server {server.id} is not valid. ' \
        f'Actual: {hostname}, expected: {valid_hostname}'


@run_only_if(platform=['!%s' % Platform.RACKSPACENGUS, '!%s' % Platform.CLOUDSTACK],
             dist=['!scientific6', '!centos-6-x', '!centos-7-x', '!coreos'])
def validate_iptables_ports(cloud: Cloud, server: Server, ports: tp.List[int], invert: bool = False):
    LOG.info(f'Verify ports {ports} in iptables')
    if CONF.feature.platform.is_cloudstack:
        LOG.info('Skip iptables check for Cloudstack')
        return
    iptables_rules = lib_server.get_iptables_rules(cloud, server)
    LOG.debug(f'iptables rules:\n{iptables_rules}')
    for port in ports:
        LOG.debug(f'Check port "{port}" in iptables rules')
        if str(port) in iptables_rules and invert:
            raise AssertionError(f'Port "{port}" in iptables rules')
        elif not invert and str(port) not in iptables_rules:
            raise AssertionError(f'Port "{port}" is NOT in iptables rules')


@run_only_if(platform=(Platform.EC2, Platform.GCE), storage='persistent')
def validate_server_message_count(context: dict, server: Server, msg: str):
    """Assert messages count with Mounted Storages count"""
    messages = lib_server.get_incoming_messages(server, msg)
    messages_count = len(messages)
    role_options = context[f'role_params_{server.farm_role_id}']
    mount_device_count = role_options.storage.volumes.count(role_options.storage)
    assert messages_count == mount_device_count, \
        f'Scalr internal messages count is wrong. ' \
        f'Actual: {messages_count}, expected: {mount_device_count}. ' \
        f'Actual messages: {messages}'


def get_config_from_message(cloud: Cloud, server: Server, config_group: str, message: str) -> dict:
    node = cloud.get_node(server)
    LOG.info('Get messages from server %s' % server.id)
    messages = lib_server.get_szr_messages(node)
    msg_id = next(filter(lambda x: x['name'] == message, messages))['id']
    LOG.info('Message id for %s is %s' % (message, msg_id))
    cmd = 'szradm message-details %s --json' % msg_id
    if CONF.feature.dist.id == 'coreos':
        cmd = "/opt/bin/" + cmd
    message_details = json.loads(node.run(cmd).std_out)['body']
    LOG.info('Message details is %s' % message_details)
    LOG.info('Returning message part %s' % config_group)
    return message_details[config_group]


def validate_message_config(cloud: Cloud, server: Server, config_group: str, message: str, old_details: dict):
    message_details = get_config_from_message(cloud, server, config_group, message)
    if old_details == message_details:
        LOG.error('New and old details is not equal: %s\n %s' % (old_details, message_details))
        raise AssertionError('New and old details is not equal')


def validate_attached_disk_types(context: dict, cloud: Cloud, farm: Farm):
    LOG.info('Verify type of attached disks')
    role = lib_role.get_role(context, farm)
    storage_config = IMPL.farm.get_role_settings(farm.id, role.role.id)['storages']
    volume_ids = {}
    attached_volumes = {}
    platform = CONF.feature.platform
    for device in storage_config['configs']:
        volume_ids[device['mountPoint']] = [s['storageId'] for s in storage_config['devices'][device['id']]]
    ids = list(chain.from_iterable(volume_ids.values()))
    volumes = list(filter(lambda x: x.id in ids, cloud.list_volumes()))
    for mount_point in volume_ids:
        attached_volumes[mount_point] = filter(lambda x: x.id in volume_ids[mount_point], volumes)
    LOG.debug('Volumes in mount points: %s' % attached_volumes)
    if platform.is_ec2:
        LOG.warning('In EC2 platform we can\'t get volume type (libcloud limits)')
        return
    elif platform.is_gce:
        diskmount = next(attached_volumes['/media/diskmount'])
        if not diskmount.extra['type'] == 'pd-standard':
            raise AssertionError('Volume attached to /media/diskmount must be "pd-standard" but it: %s' %
                                 diskmount.extra['type'])
        # if not volume_ids['/media/raidmount'][0].extra['type'] == 'pd-ssd':
        #     raise AssertionError(
        #         'Volume attached to /media/raidmount must be "pd-ssd" but it: %s' %
        #         volume_ids['/media/diskmount'][0].extra['type'])


def validate_path(cloud: Cloud, server: Server, path: str):
    LOG.info('Check directory %s' % path)
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        for attempt in range(5):
            out = conn.run('/bin/ls %s' % path)
            if out.status_code == 0:
                break
            time.sleep(15)
        else:
            LOG.error('Path %s does not exist' % path)
            raise AssertionError("'%s' does not exist on server %s" % (path, server.id))


def create_files(cloud: Cloud, server: Server, count: int, directory: str):
    node = cloud.get_node(server)
    LOG.info('Create %s files in directory %s' % (count, directory))
    node.run('cd %s && for (( i=0;i<%s;i++ )) do touch "file$i"; done' % (directory, count))


def create_partitions_on_volume(cloud: Cloud, server: Server, mnt_point: str):
    script_name = 'create_partitions.sh'
    script_src = resources(Path('scripts', script_name)).get().decode()
    path = Path('/tmp', script_name)
    node = cloud.get_node(server)

    LOG.info('Creating partitions table for volume on %s' % mnt_point)
    node.put_file(str(path), script_src % mnt_point)
    out = node.run('source %s' % path)

    partition_table = out.std_out.strip('\n').splitlines()[-4:]
    LOG.debug('Created partitions table for volume:\n%s' % '\n'.join(partition_table))
    assert all(line.startswith('/dev/') for line in partition_table), \
        'Create volume partitions failed: %s' % out.std_err
    LOG.info('Partitions table for volume was successfully created')


def create_volume_snapshot(context: dict, farm: Farm, mnt_point: str) -> str:
    device = lib_role.get_storage_device_by_mnt_point(context, farm, mnt_point)[0]
    LOG.info('Launch volume: "%s" snapshot creation' % device['storageId'])
    kwargs = dict(
        cloud_location=CONF.feature.platform.location,
        volume_id=device['storageId']
    )
    volume_snapshot_id = IMPL.aws_tools.create_volume_snapshot(**kwargs)
    assert volume_snapshot_id, 'Volume snapshot creation failed'
    LOG.info('Volume snapshot create was started. Snapshot: %s' % volume_snapshot_id)
    return volume_snapshot_id


def validate_volume_snapshot(volume_snapshot_id: str):
    def is_snapshot_completed(**kwargs):
        status = IMPL.aws_tools.snapshots_list(**kwargs)[0]['status']
        LOG.info('Wait for volume snapshot completed, actual state is: %s ' % status)
        return status == "completed"

    assert wait_until(
        is_snapshot_completed,
        kwargs=dict(
            location=CONF.feature.platform.location,
            snapshot_id=volume_snapshot_id),
        timeout=600,
        logger=LOG,
        return_bool=True), 'Volume snapshot creation failed'


def get_mount_table(cloud: Cloud, server: Server) -> tp.Dict[str, str]:
    LOG.info('Save mount table from server "%s"' % server.id)
    node = cloud.get_node(server)
    mount_table = node.run('mount').std_out.splitlines()
    mount_table = {x.split()[2]: x.split()[0] for x in mount_table if x}
    LOG.debug('Mount table:\n %s' % mount_table)
    return mount_table


def validate_mount_point_in_fstab(cloud: Cloud, server: Server, mount_table: tp.Dict[str, str], mount_point: str):
    LOG.info('Verify disk from mount point "%s" exist in fstab on server "%s"' %
             (mount_point, server.id))
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        for i in range(3):
            fstab = conn.run('cat /etc/fstab').std_out
            if not fstab:  # FIXME: on openstack this trouble was, fix this
                LOG.warning('cat /etc/fstab return nothing')
                time.sleep(15)
                continue
            break
        fstab = fstab.splitlines()
        fstab = {x.split()[1]: x.split()[0] for x in fstab if x and x.startswith('/')}
        LOG.debug('Fstab on server "%s" contains:\n %s' % (server.id, fstab))
        if mount_point not in mount_table:
            raise AssertionError('Mount point "%s" not exist in mount table:\n%s' %
                                 (mount_point, mount_table))
        if mount_point not in fstab:
            raise AssertionError('Mount point "%s" not exist in fstab:\n%s' %
                                 (mount_point, fstab))

        fstab_real_path_disk = fstab[mount_point]
        mount_real_path_disk = mount_table[mount_point]

        LOG.debug(f'Fstab and mount table state for {mount_point}: {fstab[mount_point]} {mount_table[mount_point]}')

        if 'by-uuid' in fstab[mount_point]:
            LOG.debug(f'Fstab mount point has by-uuid, get real path for {fstab[mount_point]}')
            fstab_real_path_disk = conn.run(f'readlink -f {fstab[mount_point]}').std_out.strip()
            LOG.debug(f'Fstab real path for disk: {fstab_real_path_disk}')
        elif 'by-uuid' in mount_table[mount_point]:
            LOG.debug(f'Mount point has by-uuid, get real path for {fstab[mount_point]}')
            mount_real_path_disk = conn.run(f'readlink -f {mount_table[mount_point]}').std_out.strip()
            LOG.debug(f'Mount point real path for disk: {mount_real_path_disk}')
        assert fstab_real_path_disk == mount_real_path_disk, (
                'Disk from mount != disk in fstab: "%s" != "%s"' % (mount_real_path_disk, fstab_real_path_disk))


def define_event(event_name: str):
    events = IMPL.event.list()
    res = [e for e in events if e['name'] == event_name]
    if not res:
        LOG.info('Create new Event')
        IMPL.event.change(event_name, 'Revizor FireEvent')
        events = IMPL.event.list()
        res = [e for e in events if e['name'] == event_name]
    return res[0]


def attach_script(context: dict, farm: Farm, event_name: str, script_name: str):
    scripts = IMPL.script.list()
    role = lib_role.get_role(context, farm)
    res = [s for s in scripts if s['name'] == script_name][0]
    LOG.info('Add script %s to custom event %s' % (res['name'], event_name))
    IMPL.farm.edit_role(farm.id, role.role.id, scripting=[
        {
            'scope': 'farmrole',
            'action': 'add',
            'timeout': '1200',
            'isSync': True,
            'orderIndex': 10,
            'type': 'scalr',
            'isActive': True,
            'eventName': event_name,
            'target': {
                'type': 'server'
            },
            'isFirstConfiguration': None,
            'scriptId': str(res['id']),
            'scriptName': res['name'],
            'scriptOs': 'linux',
            'version': -1,
            'scriptPath': '',
            'runAs': ''
        }]
    )


def get_device_for_additional_storage(context: dict, farm: Farm, mount_point: str):
    device_id = lib_role.get_storage_device_by_mnt_point(context, farm, mount_point)[0]['storageId']
    LOG.info('Volume Id for mount point "%s" is "%s"' % (mount_point, device_id))
    return device_id


def delete_volume(cloud: Cloud, device_id: str):
    LOG.info('Delete volume: %s' % device_id)
    volume = [v for v in cloud.list_volumes() if v.id == device_id]
    if volume:
        volume = volume[0]
    else:
        raise AssertionError('Can\'t found Volume in cloud with ID: %s' % device_id)
    for i in range(10):
        try:
            cloud._driver._conn.destroy_volume(volume)
            break
        except Exception as e:
            if 'attached' in e.message:
                LOG.warning('Volume %s currently attached to server' % device_id)
                time.sleep(60)


def validate_files_count(cloud: Cloud, server: Server, directory: str, file_count: int):
    node = cloud.get_node(server)
    LOG.info('Check count of files in directory %s' % directory)
    out = node.run('cd %s && ls' % directory).std_out.split()
    for i in ['..', '.', '...', 'lost+found']:
        if i in out:
            out.remove(i)
    if not file_count == len(out):
        raise AssertionError('Count of files in directory is not %s, is %s' % (file_count, out))


def validate_device_changed(context: dict, farm: Farm, mount_point: str, old_device_id: str):
    device = lib_role.get_storage_device_by_mnt_point(context, farm, mount_point)[0]
    if device['storageId'] == old_device_id:
        raise AssertionError('Old and new Volume Id for mount point "%s" is equally (%s)' % (mount_point, device))


def validate_scripts_launch_amt(server: Server, script_name):
    script_name = re.sub('[^A-Za-z0-9/.]+', '_', script_name)[:50]
    times = set()
    counter = 0
    server.scriptlogs.reload()
    # TODO: PP > shitty logic here, check it up later
    for script in server.scriptlogs:
        if not script.name == script_name:
            continue
        counter += 1
        times.add(script.message.splitlines()[-1].split()[-2][:-3])
    if not len(times) == counter:
        raise AssertionError('Last reboot times is equals: %s' % list(times))


def add_storage_to_role(context: dict, farm: Farm, volume_snapshot_id: str):
    role = lib_role.get_role(context, farm)
    assert volume_snapshot_id, 'No volume snapshot provided'
    LOG.info('Add volume from snapshot: %s to role' % volume_snapshot_id)
    storage_settings = {'configs': [
        {
            "id": None,
            "type": "ebs",
            "fs": None,
            "settings": {
                "ebs.size": "1",
                "ebs.type": "standard",
                "ebs.snapshot": volume_snapshot_id},
            "mount": False,
            "reUse": False,
            "status": "",
            "rebuild": False
        }
    ]}
    role.edit(storages=storage_settings)
