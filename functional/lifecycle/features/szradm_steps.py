# coding: utf-8

"""
Created on 01.22.2014
@author: Eugeny Kurkovich
"""

from lettuce import world, step
from common import LOG

from xml.etree import ElementTree as ET
from collections import defaultdict
import yaml
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

                Output dict: {'cacert': ['None', 'None', 'None'],
                               'pkey': ['None', 'None', 'None'],
                               'cert': ['None', 'None', 'None']}
        """
        if not data.startswith('+'):
            raise AssertionError('An error occurred while parsing table. Invalid data format:\n%s' % data)

        #Get table header and body
        header_end = 2
        for s_num in xrange(len(data)):
            if data[s_num] != '+':
                    continue
            elif data[s_num+2] == '|':
                header_end -= 1
            if not header_end:
                header = data[:s_num+1]
                body = data[s_num+2:]
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
                data = ET.XML(data)
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
            result[data.tag].update(('@'+key, value) for key, value in data.attrib.iteritems())
        if data.text:
            text = data.text.strip()
            if children or data.attrib:
                result[data.tag]['@text'] = text if text else ''
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


########################################
from revizor2.api import Farm
from revizor2.cloud import Cloud

farm = Farm.get(16707)

servers = farm.servers
server = farm.servers[0]
c = Cloud()

node = c.get_node(server)
#x
#lr = node.run('szradm --queryenv get-latest-version')
#t
#lr = node.run('szradm list-roles')
#t
#lr = node.run('szradm list-roles -b app')
#x
#lr = node.run('szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID')
#x
#lr = node.run('szradm --queryenv list-global-variables')
#t
lr = node.run('szradm get-https-certificate')
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
print SzrAdmResultsParser.tables_parser(lr[0])
#YAMLparser
#print SzrAdmResultsParser.yaml_parser(lr[0])
#XML parser
#print SzrAdmResultsParser.xml_parser(lr[0])
