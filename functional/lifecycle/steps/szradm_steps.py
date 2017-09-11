# coding: utf-8

"""
Created on 01.22.2014
@author: Eugeny Kurkovich
"""
import json
import time
import logging

import yaml

from xml.etree import ElementTree as ET
from collections import defaultdict
from lettuce import world, step

from revizor2.defaults import DEFAULT_ADDITIONAL_STORAGES as storages
from revizor2.conf import CONF

LOG = logging.getLogger(__name__)


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
        #TODO: Change help for more information and check if was 1 options setted with many None
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
                SzrAdmResultsParser.xml_parser(string)
        """
        try:
            if not isinstance(data, ET.Element):
                data = ET.XML(''.join(data.splitlines()).replace('\t',''))
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
        elif data.startswith('Sending SzrAdmTest'):
            return data
        else:
            raise AssertionError('An error occurred while trying get parser. Unknown data format:\n%s' % data)

    @staticmethod
    def get_values_by_key(data, key):
        """Takes a dict with nested lists and dicts,
           and searches all dicts for a key of the field
           provided.

            :param  data: Dict this parsed command result
            :type   data: dict

            :param  key: key field in dict
            :type   key: str

            >>> Usage:
                list(SzrAdmResultsParser.get_values_by_key(dict, 'key'))
        """
        if isinstance(data, list):
            for i in data:
                for x in SzrAdmResultsParser.get_values_by_key(i, key):
                    yield x
        elif isinstance(data, dict):
            if key in data:
                yield data[key]
            for j in data.values():
                for x in SzrAdmResultsParser.get_values_by_key(j, key):
                    yield x


@step(r'I run "(.*)" on ([\w]+)')
def run_command(step, command, serv_as):
    server = getattr(world, serv_as)
    node = world.cloud.get_node(server)
    LOG.info('Execute a command: %s on a remote host: %s' % (command, server.id))
    if command == 'szradm q list-farm-role-params':
        if CONF.feature.dist.is_windows:
            farm_role_id = json.loads(
                world.run_cmd_command(
                    server,
                    'szradm q list-roles --format=json')
                .std_out)['roles'][0]['id']
        else:
            farm_role_id = json.loads(node.run('szradm q list-roles --format=json')[0])['roles'][0]['id']
        command = 'szradm q list-farm-role-params farm-role-id=%s' % farm_role_id
    if CONF.feature.dist.id == 'coreos':
        command = 'PATH=$PATH:/opt/bin; ' + command
    if CONF.feature.dist.is_windows:
        result = world.run_cmd_command(server, command)
        stdout, stderr, exitcode = result.std_out, result.std_err, result.status_code
    else:
        stdout, stderr, exitcode = node.run(command)
    if exitcode:
        raise AssertionError("Command: %s, was not executed properly. An error has occurred:\n%s" %
                             (command, stderr))
    LOG.debug('Parsing a command result: %s' % stdout)
    result = SzrAdmResultsParser.parser(stdout)
    LOG.debug('Command result was successfully parsed on a remote host:%s\n%s' % (server.id, result))
    setattr(world, '%s_result' % serv_as, result)
    LOG.info('Command execution result is stored in world.%s_result' % serv_as)


@step(r'I compare(?: ([\w]+))? obtained results of ([\w\d,]+)')
def compare_results(step, fields_compare, serv_as):
    fields_compare = False if fields_compare else True
    serv_as = serv_as.split(',')
    results = []
    server_ids = []
    for i in xrange(len(serv_as)):
        server = getattr(world, serv_as[i])
        server_ids.append(server.id)
        if not fields_compare:
            results.append(getattr(world, '%s_result' % serv_as[i]))
        else:
            results.append([key for key in getattr(world, '%s_result' % serv_as[i]).iterkeys()])
    server_ids = tuple(server_ids)
    #Compare results
    if results[0] != results[1]:
        raise AssertionError('\n'.join(("An error has occurred:\n"
                                       "The results of commands on the servers %s and %s do not match." % server_ids,
                                       "Obtained results: %s" % results)))
    LOG.info('\n'.join(('Results of commands on the server %s and %s successfully compared.' % server_ids,
                        'Obtained results: %s' % results)))


@step(r'the key "(.+)" has(?: ([\w]+))? ([\d]+) record on ([\w\d]+)')
def get_key(step, pattern, denial, record_count, serv_as):
    denial = True if denial else False
    server = getattr(world, serv_as)
    results = getattr(world, '%s_result' % serv_as)
    key_value = list(SzrAdmResultsParser.get_values_by_key(results, pattern))
    key_len = len(key_value[0] if isinstance(key_value[0], list) else key_value)
    LOG.debug('Verify existence the key %s: %s in:\n%s' % (pattern, key_value, results))
    if not denial:
        if key_len != int(record_count):
            raise AssertionError("The key %s does not exists or number of entries do not match on %s" %
                                 (pattern, server.id))
    else:
        if key_len == int(record_count):
            raise AssertionError("The key %s does not exists or number of entries is match on %s" %
                                 (pattern, server.id))
    LOG.info("The key %s exists and has %s records on %s" % (pattern, record_count, server.id))


@step(r'the key "([\w\d]+)" has record "([\w\d]+)" on ([\w\d]+)')
def check_value_in_column(step, key, value, serv_as):
    results = getattr(world, '%s_result' % serv_as)
    if not value in results[key]:
        raise AssertionError('Value "%s" not exist in column "%s", all values: %s' % (value, key, results[key]))


@step(r'output contain ([\w\d]+) external ip')
def verify_external_ip(step, serv_as):
    server = getattr(world, serv_as)
    results = getattr(world, '%s_result' % serv_as)
    if not results['response']['roles']['role']['hosts']['host']['external-ip'] == server.public_ip:
        raise AssertionError('Not see server public ip in szradm response: %s' % results)


@step(r'table contains (.+) servers ([\w\d,]+)')
def search_servers_ip(step, pattern, serv_as):
    serv_as = serv_as.split(',')
    for serv_result in serv_as:
        result = getattr(world, '%s_result' % serv_result)
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

    LOG.info('Get variable %s from scalr_globals.sh on %s' % (var, server.id))
    result = node.run("grep '%s' /etc/profile.d/scalr_globals.sh" % var)
    if len(result[0].split('=')) != 2:
        raise AssertionError("Can't get variable %s from scalr_globals.sh on %s." % (var, server.id))
    script_result = result[0].split('=')[1].strip('"\n')
    #Get an variable from the environment
    LOG.info('Get variable %s from the environment on %s' % (var, server.id))
    shell = node.get_interactive()
    if not shell.recv_ready():
        time.sleep(10)
    LOG.debug('Received from shell: %s' % shell.recv(4096))

    shell.send("echo $%s\n" % var)
    if not shell.recv_ready():
        time.sleep(10)
    environment_result = shell.recv(1024)
    LOG.debug('Environment result received from %s is : %s' % (server.id, environment_result))

    if not environment_result:
        raise AssertionError("Can't get variable %s from the environment on %s." % (var, server.id))
    environment_result = environment_result.split('\r\n')[1]

    if script_result != environment_result:
        raise AssertionError("Variable %s from scalr_globals.sh does not match the environment %s on %s." %
                             (script_result, environment_result, server.id))
    LOG.info('Variable %s is checked successfully on %s' % (var, server.id))
    shell.close()


@step(r'([\w]+) has (.+) in virtual hosts configuration')
def assert_check_vhost(step, serv_as, vhost_as):
    node = world.cloud.get_node(getattr(world, serv_as))
    vhost = getattr(world, vhost_as)
    out = node.run('ls /etc/scalr/private.d/vhosts/')[0]
    if vhost.name in out:
        return True
    LOG.error('Domain %s not in vhosts, it have: %s' % (vhost.name, out))
    raise AssertionError('VHost not in apache config, in out: %s' % out)


@step(r'I set "([\w]+)" id as "([\w]+)" and run "(.*)" on ([\w\d]+)')
def set_environment_variable(step, pattern, name, command, serv_as):
    server = getattr(world, serv_as)
    result = getattr(world, '%s_result' % serv_as)
    node = world.cloud.get_node(server)
    try:
        var = result['id'][result['name'].index(pattern)]
        LOG.info('Set environment variable %s=%s and get details on a remote host: %s' % (name, var, server.id))
        result = node.run('export %(var_name)s=%(id)s && %(command)s $%(var_name)s' % {'id': var,
                                                                                       'command': command,
                                                                                       'var_name': name})
        if result[2]:
            raise AssertionError("Can't set environment variable $%s = %s or get details on a remote host: %s" %
                                 (name, var, server.id))
        result = SzrAdmResultsParser.parser(result[0])
        setattr(world, '%s_result' % serv_as, result)
        LOG.debug('Environment was successfully set up and details was saved into %s on a remote host:%s\n%s' %
                  ('%s_result' % serv_as, server.id, result))
    except (ValueError, KeyError) as e:
        raise AssertionError("Can't get %s id from command result on a remote host: %s\nError on:%s" %
                             (pattern, server.id, e))


@step(r'obtained result has all configured storages on ([\w\d]+)')
def check_volumes(step, serv_as):
    server = getattr(world, serv_as)
    node_volumes = getattr(world, '%s_result' % serv_as)['response']['volumes']['item']
    LOG.debug('Server %s configured volumes: %s' % (server.id, node_volumes))
    configured_volumes_count = len(storages.get(CONF.feature.driver.cloud_family))
    assert len(node_volumes) == configured_volumes_count, 'Server volumes mismatch'