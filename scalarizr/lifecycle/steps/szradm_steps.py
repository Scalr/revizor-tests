import json
import logging

from collections import defaultdict
from xml.etree import ElementTree as ET
import yaml

from revizor2 import CONF
from revizor2.api import Server
from revizor2.cloud import Cloud

LOG = logging.getLogger(__name__)


class SzrAdmResultsParser:
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
        for s_num in range(len(data)):
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
        for body_cell in range(len(body)):
            if (not body[body_cell]) or (body[body_cell] == 'None'):
                continue
            table[header[body_cell-(len(header)*(body_cell // len(header)))]].append(body[body_cell])
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
        except ET.ParseError as e:
            raise AssertionError('\nMessage: %s, \nInput data is:\n%s' % (e.message, data))

        result = {data.tag: {} if data.attrib else None}
        children = list(data)
        if children:
            dd = defaultdict(list)
            for dc in map(SzrAdmResultsParser.xml_parser, children):
                for key, value in dc.items():
                    dd[key].append(value)
            result = {data.tag: {key: value[0] if len(value) == 1 else value for key, value in dd.items()}}
        if data.attrib:
            result[data.tag].update((key, value) for key, value in data.attrib.items())
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
        except yaml.YAMLError as exc:
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


def run_command(cloud: Cloud, server: Server, command: str):
    node = cloud.get_node(server)
    with node.remote_connection() as conn:
        LOG.info(f'Execute a command: {command} on a remote host: {server.id}')
        if command == 'szradm q list-farm-role-params':
            farm_role_id = json.loads(conn.run('szradm q list-roles --format=json').std_out)['roles'][0]['id']
            command = f'szradm q list-farm-role-params farm-role-id={farm_role_id}'
        if CONF.feature.dist.id == 'coreos':
            command = 'PATH=$PATH:/opt/bin; ' + command
        out = conn.run(command)
        if out.status_code:
            raise AssertionError(f"Command: {command} was not executed properly. An error has occurred:\n{out.std_err}")
        LOG.debug(f'Parsing a command result: {out.std_out}')
        result = SzrAdmResultsParser.parser(out.std_out)
        LOG.debug(f'Command result was successfully parsed on a remote host:{server.id}\n{result}')
        return result


def get_key(szradm_response: dict, pattern: str) -> tuple:
    key_value = list(SzrAdmResultsParser.get_values_by_key(szradm_response, pattern))
    key_count = len(key_value[0] if isinstance(key_value[0], list) else key_value)
    return key_value, key_count
