import time
import urllib2
import logging

from lettuce import world, step

from revizor2.conf import CONF
from revizor2.api import Farm, Server, IMPL
from revizor2.consts import ServerStatus
from revizor2.utils import wait_until
from revizor2.fixtures import tables, resources
from revizor2.cloud import Cloud


LOG = logging.getLogger('haproxy')


@step(r'I add (.+) role proxying ([\w]+) ([\d]+) port to ([\w]+) role')
def add_role_to_given_farm(step, role_type, proto, port, to_role):
	'''Add role to farm and set role_type in world'''
	r = getattr(world, to_role+'_role')
	LOG.info('Add haproxy role')
	role = world.add_role_to_farm(role_type,
		options={"haproxy.listener.0": "%(proto)s#%(port)s#%(port)s#%(roleid)s" %
		                               {'proto': proto.upper(), 'port':port, 'roleid': r.id}})
	LOG.info('HAProxy role %s id %s' % (role, role.id))
	setattr(world, role_type + '_role', role)


@step(r'([\w\d]+)(?: (not))? have (.+) in backends')
def assert_check_backends(step, serv_as, have, backend_serv):
	have = False if have else True
	time.sleep(60)
	server = getattr(world, serv_as)
	backend_server = getattr(world, backend_serv)
	LOG.info('Server %s (%s) %s must be in config' % (backend_server.id, backend_server.private_ip, have))
	wait_until(check_host_haproxy, args=(server, backend_server, have), timeout=600,
	           error_text='Server %s (%s) must %s be in config' % (backend_server.id, backend_server.private_ip,
	           '' if have else 'not'))


@step(r'When I add virtual host ([\w]+)$')
def having_vhost(step, vhost_name):
	www_serv = getattr(world, 'H1')
	domain = www_serv.create_domain(www_serv.public_ip)
	app_serv = getattr(world, 'A2')
	LOG.info('Add vhost with domain %s' % domain)
	app_serv.vhost_add(domain, document_root='/var/www/%s' % vhost_name, ssl='off')
	setattr(world, vhost_name, domain)
	world.farm.vhosts.reload()
	vh = None
	for vhost in world.farm.vhosts:
		if vhost.name == domain:
			vh = vhost
	for role in world.farm.roles:
		if role.id == vh.farm_roleid:
			if 'app' in role.role.behaviors:
				return True
	raise AssertionError('Not have vhost to app role')


@step(r'([\w]+) get (.+) matches (.+) index page in (.+)$')
def check_index(step, proto, vhost_name, vhost2_name, serv_as):
	domain = getattr(world, vhost_name)
	c = Cloud()
	node = c.node_from_server(getattr(world, serv_as))
	node.run('rm /var/www/%s/index.html' % vhost_name)
	world.check_index_page(node, proto, domain, vhost2_name)
	world._domain = domain


def check_host_haproxy(server, backend_server, have=True):
	c = Cloud()
	out = c.node_from_server(server).run('cat /etc/haproxy/haproxy.cfg')[0].splitlines()
	backends = {}
	f = None
	back = []
	for line in out:
		if line.startswith('backend'):
			f = line
		elif not line.strip():
			continue
		elif line.startswith('\t') and f:
			back.append(line.strip())
		elif not line.startswith('\t') and f:
			backends[f] = back
			back = []
			f = None
	else:
		if f and back:
			backends[f] = back
	f = False
	LOG.info('Found backend sections %s' % backends)
	for backend in backends:
		for option in backends[backend]:
			if option.startswith('server'):
				if backend_server.private_ip in option:
					f = True
	LOG.debug('Server %s found in config %s' % (backend_server.private_ip, f))
	LOG.debug('%s == %s' % (have, f))
	if have == f:
		return True
	return False