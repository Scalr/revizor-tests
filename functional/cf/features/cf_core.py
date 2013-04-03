import time
import socket
from datetime import datetime
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.cloud import Cloud
from revizor2.utils import wait_until
from revizor2.fixtures import tables, resources

LOG = logging.getLogger('cloudfoundry')


@step('I add (.+) roles to this farm$')
def when_add_roles(step, roles):
    roles_list = [role.strip() for role in roles.split(',')]
    world.add_roles_to_farm(roles_list)


@step('I expect server role (.+) bootstrapping as (.+)$')
def assert_expect_server(step, role, serv_as):
    spec = 'running'
    world.farm.roles.reload()
    role_id = filter(lambda x: role.strip() in x.role.behaviors, world.farm.roles)[0]
    role_id = role_id.role_id
    server = wait_until(world.check_server_status, args=(spec, role_id, True), timeout=1500,
                        error_text="I'm not see this %s state in server" % spec)
    setattr(world, serv_as, server)


@step('cf works in (.+)$')
def assert_cf_work(step, serv_as):
    time.sleep(180)
    server = getattr(world, serv_as)
    cloud = Cloud()
    cloud_serv = cloud.node_from_server(server)
    out = cloud_serv.run("/bin/bash -c 'source /usr/local/rvm/scripts/rvm; vmc info'")[0]
    world.assert_not_in("VMware's Cloud Application Platform", out, 'CF client not work, message: %s' % out)
    #if not "VMware's Cloud Application Platform" in out:
    #       raise AssertionError('CF client not work, message: %s' % out)


@step('I add vmc user in (.+)$')
def add_user(step, serv_as):
    server = getattr(world, serv_as)
    cloud = Cloud()
    node = cloud.node_from_server(server)
    out = node.run("/bin/bash -c 'source /usr/local/rvm/scripts/rvm; vmc register --email test@test.com --passwd password'")[0]
    world.assert_not_in('Creating New User: OK', out, 'Error in user creation: %s' % out)
    #if not 'Creating New User: OK' in out[0]:
    #       raise AssertionError("Error in user creation: %s" % out)


@step('I add test app to (.+)$')
def add_test_app(step, serv_as):
    server = getattr(world, serv_as)
    cloud = Cloud()
    node = cloud.node_from_server(server)
    node.run('mkdir env')
    cont = resources('scripts/env.rb')
    node.put(path='/root/env/env.rb', content=cont.get())
    out = node.run("/bin/bash -c 'source /usr/local/rvm/scripts/rvm; vmc login --email test@test.com --passwd password; echo Y | vmc push testapp --url %s --mem 64 --path /root/env/'" % world.D1)[0]
    world.assert_not_in('Starting Application: OK', out, 'Application is not starting: %s' % out)
    #if 'Starting Application: OK' not in out[0]:
    #       raise AssertionError("Application is not starting: %s" % out)


@step(r'([\w]+) resolves into (.+) ip address')
def assert_check_resolv(step, vhost_name, serv_as, timeout=1200):
    domain = getattr(world, vhost_name)
    serv = getattr(world, serv_as)
    domain_ip = wait_until(world.check_resolving, args=(domain,), timeout=timeout, error_text="Not see domain resolve")
    world.assert_not_equal(domain_ip, serv.public_ip, 'Domain IP (%s) != server IP (%s)' % (domain_ip, serv.public_ip))


@step('([\w]+) get (.+) matches (.+) index page$')
def check_index(step, proto, vhost_name, vhost2_name):
    domain = getattr(world, vhost_name)
    wait_until(world.wait_site_response, args=(domain, 'CloudFoundry work'), timeout=1000,
               error_text="Site is not show index page")


@step('I add domain (.+) to (.+)$')
def add_domain(step, domain_as, serv_as):
    server = getattr(world, serv_as)
    domain = server.create_domain(ip=server.public_ip)
    setattr(world, domain_as, domain)
