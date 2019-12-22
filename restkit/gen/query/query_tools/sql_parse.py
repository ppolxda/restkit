# -*- coding: utf-8 -*-
"""
@create: 2017-03-31 01:32:31.

@author: name

@desc: sql_parse
"""
from __future__ import absolute_import, division, print_function
import re
import os
import json
# import functools
import sqlparse
from tornado import template


class sqlparse_error(Exception):
    """sqlparse_error."""


# ----------------------------------------------
#        field conv
# ----------------------------------------------

def __parse_field(field_str, is_table=False):  # noqa
    """__parse_field.

    conv field json
    {"field": "", "rename": "", "options":{}}
    """

    # match 'field as newfieldname'
    match_data = re.match(r'^(.*?) [Aa][Ss] ([a-zA-Z0-9_]*?)$',
                          field_str, re.IGNORECASE)
    if match_data:
        return {"field": match_data.group(1), "rename": match_data.group(2)}

    match_data = re.match(r'^([a-zA-Z0-9_]*?)\.([a-zA-Z0-9_]*?)$',
                          field_str, re.IGNORECASE)
    if match_data:
        return {"field": field_str, "rename": match_data.group(2)}

    if is_table:
        print('table_error match null %s' % field_str)
        raise sqlparse_error(
            'sql invaild, table format error({}) dbname.tablename'.format(field_str))
    else:
        match_data = re.match(
            r'^(SUM|COUNT)\(([a-zA-Z0-9_]*?)\.([a-zA-Z0-9_]*?)\)$',
            field_str, re.IGNORECASE
        )
        if match_data:
            return {"field": field_str, "rename": match_data.group(3)}

        print('field_error match null %s' % field_str)
        raise sqlparse_error('sql Alias not found({}) ex1: tablename.filedname ex2: SUM(tablename.filedname)'  # noqa
                             'ex3: COUNT(tablename.filedname) ex4: FUNC(tablename.filedname) AS filedname'.format(field_str))  # noqa


def __parse_fields(field_str):
    """__parse_fields.

    retrun [
        {"field": "", "rename": "", "cnname": "", "options":{}},
        {"field": "", "rename": "", "cnname": "", "options":{}},
    ]
    """
    result = []
    for i in range(0, len(field_str), 3):
        rename = field_str[i]
        if rename.count('.') > 1:
            raise sqlparse_error('Comment not found')

        elif rename.find('#') > 0 and rename.find(',') <= 0:
            cnname = rename.split('#')[1].strip()
            rename = rename.split('#')[0].strip()
            # raise sqlparse_error('Comment not found')
        else:
            cnname = field_str[i + 2]
            if cnname[0] != '#':
                raise sqlparse_error('Comment not found')

            cnname = cnname.split('#')[1].strip()

        options = {}
        if cnname.count('[') > 1 or cnname.count(']') > 1:
            raise sqlparse_error('parames invaild')

        if cnname.count('[') == 1 and cnname.count(']') == 1:
            options = cnname[cnname.find('[') + 1:cnname.find(']')]
            cnname = cnname[:cnname.find('[')]
            options = options.split(',')
            options = {option.split('=')[0]: option.split('=')[1]
                       for option in filter(lambda x: x != '', options)}

        rename = __parse_field(rename)
        rename['cnname'] = cnname.strip()
        rename['options'] = json.dumps(options)
        result.append(rename)
    return result


# ----------------------------------------------
#        parse field
# ----------------------------------------------


def __parse_tabless(tables_list):
    try:
        tables_list = tables_list[:tables_list.index('where')]
    except ValueError:
        pass

    result = []

    master_table = __parse_field(tables_list[0], True)
    master_table['join'] = 'master'
    master_table['on'] = ''
    result.append(master_table)

    for i in range(1, len(tables_list), 4):
        line = __parse_field(tables_list[i + 1], True)
        line.update({"join": tables_list[i], "on": tables_list[i + 3]})
        result.append(line)
    return result


# ----------------------------------------------
#        Query SQL->json
# ----------------------------------------------

def query_sql2json(sql_str):
    """query_sql2json.

    {
        "fields": [
            {"field": "", "rename": "", "cnname": "", "options":{}},
            {"field": "", "rename": "", "cnname": "", "options":{}},
        ]
        "tables": [
            {"field": "", "rename": "t0", "join": "master", "on": ""},
            {"field": "", "rename": "t1", "join": "left join", "on": ""},
            {"field": "", "rename": "t2", "join": "rigth join", "on": ""},
        ],
        "group_by": [
            'field_a',
            'field_b',
        ]
    }
    """
    assert sql_str.lower().find('select') >= 0
    # assert sql_str.lower().find('where') < 0
    assert sql_str.count(';') <= 1

    sql_str = sql_str.replace('--', '#')
    parsed = sqlparse.parse(sql_str)[0]
    parsed_list = [
        key.value
        for key in parsed.tokens
        if not key.is_whitespace and key.value != ';'
    ]

    for i, val in enumerate(parsed_list):
        if val.find('#') < 0:
            parsed_list[i] = val.lower()

    try:
        group_index = parsed_list.index('group')
        by_index = parsed_list.index('by')
    except ValueError:
        group_index = len(parsed_list)
        by_index = len(parsed_list)

    result = {
        "fields": __parse_fields(parsed_list[1: parsed_list.index('from')]),
        "tables": __parse_tabless(parsed_list[parsed_list.index('from') + 1:group_index]),  # noqa
        "group_by": []
    }

    if group_index and by_index and (group_index + 1) == by_index:
        result['group_by'] = parsed_list[by_index + 1:by_index + 2]
        result['group_by'] = result['group_by'][0].split(',')
        result['group_by'] = [key.strip() for key in result['group_by'] if key]

    return result


def query_sql2json_format(sql_str):
    """query_sql2json_format."""
    file_path = os.path.dirname(os.path.abspath(__file__))
    file_path += '../template/sql_parse_template.json'
    faile_format = template.Template(open(file_path, 'r').read())
    return faile_format.generate(**query_sql2json(sql_str))


def json_format(val):
    for field in val["fields"]:
        if 'options' not in field:
            field['options'] = '{}'
        else:
            field['options'] = json.dumps(field['options'])

        if 'cnname' not in field:
            field['cnname'] = ''

    file_path = os.path.dirname(os.path.abspath(__file__))
    file_path += '../template/sql_parse_template.json'
    faile_format = template.Template(open(file_path, 'r').read())
    return faile_format.generate(**val)

# ----------------------------------------------
#        Query SQL<-json
# ----------------------------------------------


def json2query_sql(json_dict, need_group_by=False, no_cnname=False):
    """json2query_sql.

    {
        "fields": [
            {"field": "", "rename": "", "cnname": "", "options":{}},
            {"field": "", "rename": "", "cnname": "", "options":{}},
        ]
        "tables": [
            {"field": "", "rename": "t0", "join": "master", "on": ""},
            {"field": "", "rename": "t1", "join": "left join", "on": ""},
            {"field": "", "rename": "t2", "join": "rigth join", "on": ""},
        ],
        "group_by": [
            'field_a',
            'field_b',
        ]
    }
    """
    assert isinstance(
        json_dict, dict) and 'fields' in json_dict and 'tables' in json_dict

    field_keys = [
        line['field']
        for line in json_dict['fields']
        if not line.get('options', {}).get('select', False) and
        not line.get('options', {}).get('query_only', False)
    ]

    def dot_add(line, lists):
        line['dot'] = ','
        if line['field'] == field_keys[-1]:
            line['dot'] = ''

        if 'options' in line and line['options']:
            if not isinstance(line['options'], dict):
                raise sqlparse_error('options type not dict')
            line['options_str'] = ','.join(
                ['{}={}'.format(key, val)
                 for key, val in line['options'].items()])
            line['options_str'] = '[' + line['options_str'] + ']'
        else:
            line['options_str'] = ''

        return line

    if no_cnname:
        field_sql = ' '.join([
            '%(field)s as %(rename)s%(dot)s' %
            dot_add(line, json_dict['fields'])
            for line in json_dict['fields']
            if not line.get('options', {}).get('select', False) and
            not line.get('options', {}).get('query_only', False)
        ])
    else:
        field_sql = '\n'.join(
            ['%(field)s as %(rename)s%(dot)s  -- %(cnname)s %(options_str)s' %
             dot_add(line, json_dict['fields'])
             for line in json_dict['fields']])

    table_sql = ' '.join(['%(join)s %(field)s as %(rename)s on %(on)s' %
                          line for line in json_dict['tables'][1:]])
    table_sql = ('%(field)s as %(rename)s ' %
                 json_dict['tables'][0]) + table_sql

    group_sql = ''
    if need_group_by and json_dict['group_by']:
        group_sql = ', '.join(json_dict['group_by'])
        group_sql = ' GROUP BY ' + group_sql

    return 'SELECT %s FROM %s%s' % (field_sql, table_sql, group_sql)


def json2query_sql_format(json_dict, need_group_by=False, no_cnname=False):
    sqlcode = json2query_sql(json_dict, need_group_by, no_cnname)
    return sqlparse.format(sqlcode, reindent=True)


def sql_format(val):
    return sqlparse.format(val, reindent=True)


def json_file2query_sql(file_path):
    """json_file2query_sql."""
    return json2query_sql(json.loads(open(file_path, 'r').read()))
