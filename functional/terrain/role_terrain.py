__author__ = 'gigimon'
import os
import time
import logging
from datetime import datetime

from lettuce import world, step

from revizor2.api import Role
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.dbmsr import Database
from revizor2.consts import Platform


LOG = logging.getLogger(__name__)


@step('I change branch to system for (\w+) role')
def change_branch_in_role_for_system(step, role):
    """Change branch for selected role"""
    LOG.info('Change branch to system for %s role' % role)
    role = getattr(world, '%s_role' % role)
    role.edit(options={"user-data.scm_branch": CONF.feature.branch})


@step('I increase minimum servers to (.+) for (.+) role')
def increase_instances(step, count, role_type):
    """Increase minimum servers count for role"""
    role = getattr(world, '%s_role' % role_type)
    options = {"scaling.max_instances": int(count) + 1,
               "scaling.min_instances": count}
    world.farm.edit_role(role.role_id, options)


@step('I know ([\w]+) storages$')
def get_ebs_for_instance(step, serv_as):
    """Give EBS storages for server"""
    #TODO: Add support for rackspaceng
    server = getattr(world, serv_as)
    volumes = server.get_volumes()
    LOG.debug('Volumes for server %s is: %s' % (server.id, volumes))
    if CONF.feature.driver.current_cloud == Platform.EC2:
        storages = filter(lambda x: 'sda' not in x.extra['device'], volumes)
    elif CONF.feature.driver.current_cloud in [Platform.IDCF, Platform.CLOUDSTACK]:
        storages = filter(lambda x: x.extra['type'] == 'DATADISK', volumes)
    else:
        return
    LOG.info('Storages for server %s is: %s' % (server.id, storages))
    if not storages:
        raise AssertionError('Server %s not have storages (%s)' % (server.id, storages))
    setattr(world, '%s_storages' % serv_as, storages)


@step('([\w]+) storage is (.+)$')
def check_ebs_status(step, serv_as, status):
    """Check EBS storage status"""
    if CONF.feature.driver.current_cloud == Platform.GCE:
        return
    time.sleep(30)
    server = getattr(world, serv_as)
    wait_until(world.check_server_storage, args=(serv_as, status), timeout=300, error_text='Volume from server %s is not %s' % (server.id, status))


@step('I create server snapshot for ([\w]+)$')
def rebundle_server(step, serv_as):
    """Start rebundle for server"""
    serv = getattr(world, serv_as)
    name = 'tmp-%s-%s' % (serv.role.name, datetime.now().strftime('%m%d%H%M'))
    bundle_id = serv.create_snapshot('no_replace', name)
    if bundle_id:
        world.bundle_id = bundle_id


@step('Bundle task created for ([\w]+)')
def assert_bundletask_created(step, serv_as):
    """Check bundle task status"""
    serv = getattr(world, serv_as)
    world.bundle_task_created(serv, world.bundle_id)


@step('Bundle task becomes completed for ([\w]+)')
def assert_bundletask_completed(step, serv_as, timeout=1800):
    serv = getattr(world, serv_as)
    wait_until(world.bundle_task_completed, args=(serv, world.bundle_id), timeout=timeout, error_text="Bundle not completed")


@step('I add to farm role created by last bundle task')
def add_new_role_to_farm(step):
    options = getattr(world, 'role_options', {})
    scripting = getattr(world, 'role_scripting', [])
    bundled_role = Role.get(world.bundled_role_id)
    if 'redis' in bundled_role.behaviors:
        options.update({'db.msr.redis.persistence_type': os.environ.get('RV_REDIS_SNAPSHOTTING', 'aof'),
                        'db.msr.redis.use_password': True})
    world.farm.add_role(world.bundled_role_id, options=options, scripting=scripting)
    world.farm.roles.reload()
    role = world.farm.roles[0]
    setattr(world, bundled_role.behaviors_as_text() + '_role', role)
    LOG.info("Set DB object to world")
    if {bundled_role.behaviors}.intersection(['mysql', 'mariadb', 'percona', 'mysql2', 'percona2',
                                              'postgresql', 'redis', 'mongodb']):
        db = Database.create(role)
        if db:
            setattr(world, 'db', db)