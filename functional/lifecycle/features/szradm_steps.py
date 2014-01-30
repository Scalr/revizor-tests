# coding: utf-8

"""
Created on 01.22.2014
@author: Eugeny Kurkovich
"""

import logging
import yaml
from xml.etree import ElementTree as ET
from collections import defaultdict
from lettuce import world, step

LOG = logging.getLogger('SzrAdm')
########################################


class SzrAdmResultsParser(object):

    @staticmethod
    def tables_parser(data):
        """Convert input formatted string to dict this keys from table headers.
            Return dict {table header[1]: [table rows[1:]], table header[n]: [table rows[1:]}
            :param  data: formatted string
            :type   data: str

            >>> Usage:
                SzrAdmResultsParser.tables_parser(string)

                Input string:
                +------+------+--------+
                | cert | pkey | cacert |
                +------+------+--------+
                | None | None |  None  |
                | None | None |  None  |
                | None | None |  None  |
                +------+------+--------+

                Output dict: {'cacert': [],
                               'pkey': [],
                               'cert': []}
        """
        if not data.startswith('+'):
            raise AssertionError('An error occurred while parsing table. Invalid data format:\n%s' % data)

        #Set header lines count
        header_end = 3
        #Get table header and body
        for s_num in xrange(len(data)):
            if data[s_num] != '\n':
                continue
            header_end -= 1

            if not header_end:
                header = data[:s_num]
                body = data[s_num+1:]
                break
        #Get header elements [cel1, cel2, cel...n]
        table = {}
        for line in header.splitlines():
            if line.startswith('+'):
                continue
            header = [row.strip() for row in line.strip('|').split('|')]
            table = {item: [] for item in header}
            break
        #Get body elements [cel1, cel2, cel...n]
        body = [line.strip() for line in body.strip('|').split('|') if len(line.strip()) and not line.strip().startswith('+')]
        #Set output result
        for body_cell in xrange(len(body)):
            if (not body[body_cell]) or (body[body_cell] == 'None'):
                continue
            table[header[body_cell-(len(header)*(body_cell / len(header)))]].append(body[body_cell])
        return table

    @staticmethod
    def xml_parser(data):
        """Convert input xml formatted string. Return dict .
            :param  data: xml formatted string
            :type   data: str

            >>> Usage:
                SzrAdmResultsParser.yaml_parser(string)
        """
        try:
            if not isinstance(data, ET.Element):
                data = ET.XML(data.translate(None, '\n\t'))
        except ET.ParseError, e:
            raise AssertionError('\nMessage: %s, \nInput data is:\n%s' % (e.message, data))

        result = {data.tag: {} if data.attrib else None}
        children = list(data)
        if children:
            dd = defaultdict(list)
            for dc in map(SzrAdmResultsParser.xml_parser, children):
                for key, value in dc.iteritems():
                    dd[key].append(value)
            result = {data.tag: {key: value[0] if len(value) == 1 else value for key, value in dd.iteritems()}}
        if data.attrib:
            result[data.tag].update((key, value) for key, value in data.attrib.iteritems())
        if data.text:
            text = data.text.strip()
            if children or data.attrib:
                result[data.tag]['text'] = text if text else ''
            else:
                result[data.tag] = text
        return result

    @staticmethod
    def yaml_parser(data):
        """Convert input yaml formatted string. Return dict .
           If there are no data in the input, it returns None.

            :param  data: yaml formatted string
            :type   data: str

            >>> Usage:
                SzrAdmResultsParser.yaml_parser(string)
        """
        try:
            return yaml.load(data)
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                mark_line, mark_column = exc.problem_mark.line+1, exc.problem_mark.column+1
                raise AssertionError('\nMessage: An error occurred while parsing yaml.\n'
                                     'Error position:(%s:%s)\n'
                                     'Input data is:\n%s' % (mark_line, mark_column, data))

    @staticmethod
    def parser(data):

        if data.startswith('+----'):
            return SzrAdmResultsParser.tables_parser(data)
        elif data.startswith('<?xml'):
            return SzrAdmResultsParser.xml_parser(data)
        elif data.startswith('body:'):
            return SzrAdmResultsParser.yaml_parser(data)
        else:
            raise AssertionError('An error occurred while trying get parser. Unknown data format:\n%s' % data)

    @staticmethod
    def get_value(data, key):
        """Takes a dict with nested lists and dicts,
           and searches all dicts for a key of the field
           provided.

            :param  data: Dict this parsed command result
            :type   data: dict

            :param  key: key field in dict
            :type   key: str

            >>> Usage:
                list(SzrAdmResultsParser.get_value(dict, 'key'))
        """
        if isinstance(data, list):
            for i in data:
                for x in SzrAdmResultsParser.get_value(i, key):
                    yield x
        elif isinstance(data, dict):
            if key in data:
                yield data[key]
            for j in data.values():
                for x in SzrAdmResultsParser.get_value(j, key):
                    yield x

#########################################


@step(r'I run "(.*)" on ([\w]+)')
def run_command(step, command, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Execute a command: %s on a remote server: %s' % (command, server.id))
    result = node.run(command)
    if result[2]:
        error_text = "Сommand: %s, was not executed properly. An error has occurred:\n%s" % (command, result[1])
        LOG.error(error_text)
        raise AssertionError(error_text)
    setattr(world, '%s_result' % serv_as, result[0])
    LOG.debug('Command execution result is stored in world.%s_result:\n%s' % (serv_as, result[0]))


@step(r'I compare the obtained results of ([\w\d,]+)')
def compare_results(step, serv_as):

    serv_as = serv_as.split(',')
    results = {}
    id = []
    for i in xrange(len(serv_as)):
        server = getattr(world, serv_as[i])
        id.append(server.id)
        LOG.debug('Parsing a command result on a remote server: %s' % server.id)
        results.update({serv_as[i]: SzrAdmResultsParser.parser(getattr(world, '%s_result' % serv_as[i]))})
        LOG.debug('Command result was successfully parsed on a remote server:%s\n%s' % (server.id, results[serv_as[i]]))
    id = tuple(id)
    LOG.debug(results)
    #Compare results
    if results.values()[0] != results.values()[1]:
        raise AssertionError("An error has occurred:\n"
                             "The results of commands on the servers %s and %s do not match." % id)
    setattr(world, 'results', results)
    LOG.info('Results of commands on the server %s and %s successfully compared' % id)


@step(r'the key "(.+)" has ([\d]+) record on ([\w\d]+)')
def get_key(step, pattern, record_count, serv_as):
    server = getattr(world, serv_as)
    results = getattr(world, 'results')[serv_as]
    key_value = list(SzrAdmResultsParser.get_value(results, pattern))
    LOG.debug('Verify existence the key %s: %s in:\n%s' % (pattern, key_value, results))
    if len(key_value) != int(record_count):
        raise AssertionError("The key %s does not exists or has an empty result on %s" % (pattern, server.id))
    LOG.info("The key %s exists and not is empty on %s" % (pattern, server.id))


@step(r'table contains (.+) servers ([\w\d,]+)')
def search_servers_ip(step, pattern, serv_as):
    serv_as = serv_as.split(',')
    results = getattr(world, 'results')
    for serv_result in serv_as:
        result = results[serv_result]
        LOG.debug('Checking the ip address entry in result on the server %s' % getattr(world, serv_result).id)
        for serv in serv_as:
            server_ip = getattr(world, serv).public_ip
            LOG.debug('Checking the ip address: %s' % server_ip)
            if not (server_ip in result[pattern]):
                raise AssertionError('IP address: %s '
                                     'is not included in the table of results: %s' % (server_ip, result[pattern]))
        else:
            LOG.info('Table: %s contains all verified address.' % result[pattern])


@step(r'I check an variable "(.+)" on ([\w\d]+)')
def check_variable(step, var, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    #Get an variable from script /etc/profile.d/scalr_globals.
    LOG.info('Get variable %s from scalr_globals.sh on %s' % (var, server.id))
    result = node.run("grep '%s' /etc/profile.d/scalr_globals.sh" % var)
    if len(result[0].split('=')) != 2:
        raise AssertionError("Can't get variable %s from scalr_globals.sh on %s." % (var, server.id))
    script_result = result[0].split('=')[1].strip('"')
    #Get an variable from the environment
    LOG.info('Get variable %s from the environment on %s' % (var, server.id))
    result = node.run("env | grep '%s'" % var)
    if len(result[0].split('=')) != 2:
        raise AssertionError("Can't get variable %s from the environment on %s." % (var, server.id))
    environment_result = result[0].split('=')[1]
    if script_result != environment_result:
        raise AssertionError("Variable %s from scalr_globals.sh does not match the environment %s on %s." % (script_result, environment_result, server.id))
    LOG.info('Variable %s is checked successfully on %s' % (var, server.id))


@step('I create domain ([\w\d]+) to ([\w\d]+) role')
def create_domain_to_role(step, domain_as, role):
    LOG.info('Create new domain for role %s as %s' % (role, domain_as))
    role = getattr(world, '%s_role' % role)
    domain = role.create_domain()
    LOG.info('New domain: %s' % domain.name)
    setattr(world, domain_as, domain)


@step('I add(?: (ssl))? virtual host ([\w\d]+)(?: with key ([\w\d-]+))? to ([\w\d]+) role and domain ([\w\d]+)')
def create_vhost_to_role(step, ssl, vhost_as, key_name, role, domain_as):
    ssl = True if ssl else False
    key_name = key_name if key_name else None
    role = getattr(world, '%s_role' % role)
    domain = getattr(world, domain_as)
    LOG.info('Add new virtual host for role %s, domain %s as %s %s' % (role, domain.name, vhost_as,
                                                                       'with key {0}'.format(key_name)
                                                                       if key_name
                                                                       else ''))
    vhost = role.add_vhost(domain.name, document_root='/var/www/%s' % vhost_as, ssl=ssl, cert=key_name)
    setattr(world, vhost_as, vhost)


@step(r'([\w]+) has (.+) in virtual hosts configuration')
def assert_check_vhost(step, serv_as, vhost_as):
    node = world.cloud.get_node(getattr(world, serv_as))
    vhost = getattr(world, vhost_as)
    out = node.run('ls /etc/scalr/private.d/vhosts/')[0]
    if vhost.name in out:
        return True
    LOG.error('Domain %s not in vhosts, it have: %s' % (vhost.name, out))
    raise AssertionError('VHost not in apache config, in out: %s' % out)

#########################################


# from revizor2.api import Farm
# from revizor2.cloud import Cloud
# farm = Farm.get(16707)
#
# servers = farm.servers
# server = farm.servers[0]
# c = Cloud()
#
# node = c.get_node(server)
# #x
#lr = node.run('szradm --queryenv get-latest-version')
#t
#lr = node.run('szradm list-roles')
#t
#lr = node.run('szradm list-roles -b app')
#lr = node.run('szradm list-roles -b base')
#x
#lr = node.run('szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID')
#x
#lr = node.run('szradm --queryenv list-global-variables')
#t
#lr = node.run('szradm get-https-certificate')
#t
#lr = node.run('szradm list-virtualhosts')
#t
#lr = node.run('szradm list-ebs-mountpoints')
#t
#lr = node.run('szradm list-messages')
#y
#lr = node.run('szradm message-details c456fda9-b071-4270-b5a7-c0e7ed6623fc')
########################################

#print lr[0]

#Table parser
#print SzrAdmResultsParser.tables_parser(lr[0])
#YAMLparser
#print SzrAdmResultsParser.yaml_parser(lr[0])
#XML parser
#print list(SzrAdmResultsParser.get_value(SzrAdmResultsParser.xml_parser(lr[0]), 'behaviour'))
#print SzrAdmResultsParser.xml_parser(lr[0])