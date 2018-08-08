import logging

from revizor2.api import Server

LOG = logging.getLogger(__name__)


# @world.run_only_if(platform='!%s' % Platform.VMWARE) <-- TODO
def validate_instance_vcpus_info(server: Server):
    vcpus = int(server.details['info.instance_vcpus'])
    LOG.info(f'Server {server.id} vcpus info: {vcpus}')
    assert vcpus > 0, f'info.instance_vcpus not valid for {server.id}'


# @world.run_only_if(platform=(Platform.EC2, Platform.GCE), storage='persistent') <-- TODO
def assert_server_message_count(context: dict, server: Server, msg: str):
    """Assert messages count with Mounted Storages count"""
    server.messages.reload()
    incoming_messages = [m.name for m in server.messages if m.type == 'in' and m.name == msg]
    messages_count = len(incoming_messages)
    role_options = context[f'role_params_{server.farm_role_id}']
    mount_device_count = role_options.storage.volumes.count(role_options.storage)
    assert messages_count == mount_device_count, \
        f'Scalr internal messages count {messages_count} != {mount_device_count} Mounted storages count. ' \
        f'List of all Incoming msg names: {incoming_messages}'
