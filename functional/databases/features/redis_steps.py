from lettuce import world, step

import logging


LOG = logging.getLogger('redis')


@step('And ([^ .]+) is slave of ([^ .]+)')
def assert_check_slave(step, slave_serv, master_serv):
	slave_server = getattr(world, slave_serv)
	master_server = getattr(world, master_serv)
	slaves = world.db.get_slaves()
	master = world.db.get_master()
	for s in slaves:
		if slave_server.id == s.id:
			if master_server.id == master.id:
				return True
			else:
				raise AssertionError("Server %s is not master" % master.id)
	raise AssertionError("Server %s is not slave" % slave_server.id)
