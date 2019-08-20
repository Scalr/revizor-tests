import re
import json
import logging
from datetime import datetime
from revizor2.conf import CONF

from revizor2.api import Server
from revizor2.utils import wait_until


LOG = logging.getLogger(__name__)


def start_server_rebundle(server: Server) -> int:
    """Start rebundle for server"""
    name = 'tmp-%s-%s' % (server.role.name, datetime.now().strftime('%m%d%H%M'))
    kwargs = dict(
        name=name
    )
    if CONF.feature.platform.is_vmware:
        farm_role_settings = next(filter(
            lambda r: int(r['farm_role_id']) == int(server.farm_role_id),
            server.farm.settings['farm']['roles']))['settings']
        kwargs.update(dict(
            vmware_folder=farm_role_settings['vmware.folder'],
            vmware_compute_resource=farm_role_settings['vmware.compute_resource'],
            vmware_host=json.loads(farm_role_settings['vmware.host_system']),
            vmware_datastore=farm_role_settings['vmware.datastore']))
    bundle_id = server.create_snapshot(**kwargs)
    return bundle_id


def assert_bundle_task_created(server: Server, bundle_id: int):
    contents = None
    for bundlelog in server.bundlelogs:
        if bundlelog.id == bundle_id:
            contents = bundlelog.contents
            break
    if contents:
        for log in contents:
            if 'Bundle task created' in log['message']:
                LOG.info(f'Bundle task for server {server.id} was created with id: {bundle_id}')
                return True
            elif 'Bundle task status changed to: failed' in log['message']:
                LOG.error(f'Bundle task for server {server.id} with id {bundle_id} was failed with error: {log["message"]}')
                raise AssertionError(log['message'])
    return AssertionError(f"Can't find bundle task for server {server.id}")


def wait_bundle_complete(server: Server, bundle_id: int) -> int:
    def check_bundle_complete():
        server.bundlelogs.reload()
        for bundlelog in server.bundlelogs:
            if bundlelog.id == bundle_id:
                contents = bundlelog.contents
                for log in contents:
                    if 'Bundle task status: success' in log['message']:
                        for l in contents:
                            if 'Role ID:' in l['message']:
                                role_id = re.findall(r"Role ID: ([\d]+)", l['message'])[0]
                        LOG.info(f'Bundle task {bundle_id} is complete. New role id: {role_id}')
                        return role_id
                    elif 'Bundle task status changed to: failed' in log['message']:
                        raise AssertionError(log['message'])
        return False
    return wait_until(check_bundle_complete, timeout=1800,
                      error_text=f'Bundle task {bundle_id} not finished after 30 minutes')

