# coding: utf-8

"""
Created on 01.22.2014
@author: Eugeny Kurkovich
"""

from lettuce import world, step
from xml.etree import cElementTree as ET
from collections import defaultdict
from common import LOG
import yaml
########################################


class SzrAdmResultsParser(object):

    @staticmethod
    def tables_parser(data):
        """Convert input formatted string to dict this keys from table headers.
            Return dist {table header[1]: [table rows[1:]], table header[n]: [table rows[1:]}
            :param  data: formatted string
            :type   data:str

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

        #Convert table to dict result {table header[1]: [table rows[1:]], table header[n]: [table rows[1:]}
        table = {}
        for row_cell in xrange(len(lines[0])):
            table.update({lines[0][row_cell]: []})
            for table_row in xrange(len(lines[1:])):
                table[lines[0][row_cell]].append(lines[table_row+1][row_cell])
        return table

    @staticmethod
    def xml_parser(data):
        d = {data.tag: {} if data.attrib else None}
        children = list(data)
        if children:
            dd = defaultdict(list)
            for dc in map(SzrAdmResultsParser.xml_parser, children):
                for k, v in dc.iteritems():
                    dd[k].append(v)
            d = {data.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
        if data.attrib:
            d[data.tag].update(('@' + k, v) for k, v in data.attrib.iteritems())
        if data.text:
            text = data.text.strip()
            if children or data.attrib:
                if text:
                  d[data.tag]['#text'] = text
            else:
                d[data.tag] = text
        return d

    @staticmethod
    def yaml_parser(data):
        """Convert input yaml formatted string. Return dict .
           If there are no data in the input, it returns None.

            :param  data: yaml formatted string
            :type   data:str

            >>> Usage:
                SzrAdmResultsParser.yaml_parser(string)
        """
        try:
            return yaml.load(data)
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                mark_line, mark_column = exc.problem_mark.line+1, exc.problem_mark.column+1
                raise AssertionError('An error occurred while parsing yaml. Error position:(%s:%s) on:%s' % (mark_line, mark_column, data))


########################################
from revizor2.api import Farm
from revizor2.cloud import Cloud

farm = Farm.get(16707)

servers = farm.servers
server = farm.servers[0]
c = Cloud()

node = c.get_node(server)
#lr = node.run('szradm --queryenv get-latest-version')
#lr = node.run('szradm --queryenv list-global-variables')
lr = node.run('szradm --queryenv list-roles farm-role-id=$SCALR_FARM_ROLE_ID')
#lr = node.run('szradm list-roles')
#lr = node.run('szradm message-details 050b5417-1486-4562-b630-c33ee996b709')
########################################


#print SzrAdmResultsParser.tables_parser(lr[0])
#print SzrAdmResultsParser.yaml_parser(lr[0])
print SzrAdmResultsParser.xml_parser(ET.XML(lr[0]))