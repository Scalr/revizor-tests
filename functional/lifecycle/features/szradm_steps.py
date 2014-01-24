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
            Return dist {table header[1]: [table rows[1:]], table header[n]: [table rows[1:]}
            :param  data: formatted string
            :type   data: str

            >>> Usage:
                SzrAdmResultsParser.tables_parser(string)
        """
        if not data.startswith('+'):
            raise AssertionError('An error occurred while parsing table. Invalid data format:\n%s' % data)

        #Get table lines, result [[line1], [line1]]
        lines = []
        for line in data.splitlines():
            if line.startswith('+'):
                continue
            lines.append([row.strip() for row in line.strip('|').split('|')])
        #Combines multi-line table cells
        combi_lines = [lines.pop(0)]
        for line_num in xrange(len(lines)):
            if len(lines[line_num]) == len(combi_lines[0]):
                combi_lines.append(lines[line_num])
            else:
                combi_lines[-1][-1] = '\n'.join((combi_lines[-1][-1], lines[line_num][0]))
        del lines
        #Convert table to dict result {table header[1]: [table rows[1:]], table header[n]: [table rows[1:]}
        table = {}
        for row_cell in xrange(len(combi_lines[0])):
            table.update({combi_lines[0][row_cell]: []})
            for table_row in xrange(len(combi_lines[1:])):
                table[combi_lines[0][row_cell]].append(combi_lines[table_row+1][row_cell])

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
#lr = node.run('szradm get-https-certificate')
#t
#lr = node.run('szradm list-virtualhosts')
#t
#lr = node.run('szradm list-ebs-mountpoints')
#t
lr = node.run('szradm list-messages')
#y
#lr = node.run('szradm message-details c456fda9-b071-4270-b5a7-c0e7ed6623fc')
########################################

print lr[0]

#Table parser
print SzrAdmResultsParser.tables_parser(lr[0])
#YAMLparser
#print SzrAdmResultsParser.yaml_parser(lr[0])
#XML parser
#print SzrAdmResultsParser.xml_parser(lr[0])
