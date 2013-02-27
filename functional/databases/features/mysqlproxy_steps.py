import re
import time

import MySQLdb as mysql

from lettuce import world, step

from revizor2.utils import wait_until
from revizor2.cloud import Cloud
import logging


LOG = logging.getLogger('mysqlproxy')


@step('And ([\w\d]+) is (.+) in ([\w\d]+)$')
def assert_proxy_record(step, client_as, client_type, server_as):
	time.sleep(60)
	client = getattr(world, client_as)
	server = getattr(world, server_as)
	cloud = Cloud()
	cloud_serv = cloud.get_node(server)
	out = cloud_serv.run('cat /etc/mysql_proxy.conf')
	t = 'proxy-backend-addresses' if client_type == 'writer' else 'proxy-read-only-backend-addresses'
	clients = re.findall('%s\t= (.+)' % t, out[0])
	if not client.private_ip in "".join(clients):
		raise AssertionError('%s not in config, file content: %s' % (client.private_ip, out))


@step('When I write data to ([\w\d]+)$')
def write_data_to_db(step, serv_as):
	server = getattr(world, serv_as)
	passw = world.db._password
	m_db = mysql.connect(host=server.public_ip,
				port=4040,
				user='scalr',
				passwd=passw,
				db='D1')
	m_cursor = m_db.cursor()
	m_cursor.execute("""CREATE TABLE table1 (
						test VARCHAR( 255 ) NOT NULL 
						) ENGINE = MYISAM ;""")
	m_cursor.execute("""INSERT INTO table1 (test)
						VALUES ('mysql_proxy_test');""")


@step('I read data from (P1|P2)$')
def read_data_from_db(step, serv_as):
	server = getattr(world, serv_as)
	passw = world.db._password
	m_db = mysql.connect(host=server.public_ip,
				port=4040,
				user='scalr',
				passwd=passw,
				db='D1')
	m_cursor = m_db.cursor()
	l = m_cursor.execute("""SELECT * FROM table1""")
	if l > 0:
		return True
	

@step('data in (.+)$')
def check_data(step, serv_as):
	server = getattr(world, serv_as)
	passw = world.db._password
	m_db = mysql.connect(host=server.public_ip,
				port=3306,
				user='scalr',
				passwd=passw,
				db='D1')
	m_cursor = m_db.cursor()
	l = m_cursor.execute("""SELECT * FROM table1""")
	if l > 0:
		return True


@step('([\w\d]+) not in (.+) config$')
def not_in_config(step, serv_as, serv_config):
	time.sleep(180)
	server = getattr(world, serv_as)
	server_config = getattr(world, serv_config)
	cloud = Cloud()
	cloud_serv = cloud.get_node(server_config)
	wait_until(check_not_in_config, args=(cloud_serv, server), timeout=1200, error_text='%s with IP %s in config' %
	                                                                                   (serv_as, server.private_ip))


def check_not_in_config(node, server):
	out = node.run('cat /etc/mysql_proxy.conf')[0]
	if server.private_ip in out:
		return False
	return True
