# -*- coding: utf-8 -*-
"""
@create: 2017-10-13 11:10:34.

@author: name

@desc: template_maker
"""
import re
import os
import json
import codecs
from tornado import template
from tornado.options import options, define

FPAHT_DEFINE = '${fpath}'
FPATH = os.path.abspath(os.path.dirname(__file__))


# try:
#     from functools import reduce
# except ImportError:
#     pass

# define('fs_mode', 'index', str)
define('fs_in', './out/administrate.proto.json', str)
define('fs_out', './out/administrate.sql', str)
define('fs_tmpl',
       '${fpath}/template/init_sql/create_table_index_tmpl.sql', str)
# define('fs_tmpl_name', 'create_table_tmpl.sql', str)
define('fs_dbname', 'test_sql', str)


UINT_LIST = ['uint16']
FLOAT_LIST = ['double8_4', 'double16_6', 'double36_14',
              'double16_2', 'double24_8', 'amount_type']
STRING_LIST = ['string4', 'string8', 'string12', 'string16',
               'string24', 'string32', 'string64', 'string128',
               'string256', 'string512', 'string2048', 'jsonString']
BYTE_LIST = ['byte24']


def get_comments(field, key):
    if 'comments' not in field:
        return key
    if key not in field['comments']:
        return key
    return field['comments'][key]


def make_model_name(table, space_characters='_'):
    model = re.sub(r'[^\w]+', '', table)
    model_name = ''.join(sub.title()
                         for sub in model.split(space_characters))
    if not model_name[0].isalpha():
        model_name = 'T' + model_name
    return model_name


def generate_file(tmpl_path, file_path, **kwarg):
    """generate_file."""
    # template_loader = template.Loader(options.fs_tmpl)
    tmpl_path = tmpl_path.replace(FPAHT_DEFINE, FPATH)
    with codecs.open(tmpl_path, 'rb') as fs:
        tmpl = fs.read()
    make_data = template.Template(tmpl).generate(**kwarg)
    save_file(file_path, make_data)
    return make_data


def init_table_json(_json_table):
    assert isinstance(_json_table, dict)

    for tables in _json_table.values():
        if 'nested' not in tables:
            tables['nested'] = {}

        if 'fields' not in tables:
            print('no fields:', tables)
            continue

        for field in tables['fields'].values():
            if 'options' not in field:
                field['options'] = {}

            if 'default' not in field['options']:
                field['options']['default'] = None

            if field['options']['default'] == '"now"' and\
                    field['type'] == 'datetime':
                field['options']['default'] = 'CURRENT_TIMESTAMP'

            if field['options']['default'] == '"now"' and\
                    field['type'] == 'date':
                field['options']['default'] = ''

            if field['type'] in UINT_LIST:
                field['options']['maxlen'] = str(
                    int(field['type'][len('byte'):]))

            if field['type'] in BYTE_LIST:
                field['options']['maxlen'] = str(
                    int(field['type'][len('byte'):]))

            if field['type'] in STRING_LIST:
                if field['type'] == 'jsonString':
                    field['options']['maxlen'] = '512'
                else:
                    field['options']['maxlen'] = str(
                        int(field['type'][len('string'):]))

            if field['type'] in FLOAT_LIST:
                if field['type'] == 'amount_type':
                    field['options']['maxlen'] = '36,10'
                else:
                    field['options']['maxlen'] = str(
                        int(field['type'][len('double'):])).replace('_', ',')

            if 'maxlen' not in field['options']:
                field['options']['maxlen'] = None

            if 'key' not in field['options']:
                field['options']['key'] = False

            if 'inc' not in field['options']:
                field['options']['inc'] = False

            if 'update' not in field['options']:
                field['options']['update'] = False

        tables['keys'] = [key for key, val in tables['fields'].items()
                          if bool(val['options'].get('key', False))]
    return _json_table


def make_table_init_sql(_json_table: dict, _json_enum: dict):
    """make_table_init_sql."""
    generate_file(options.fs_tmpl,
                  options.fs_out,
                  dbname=options.fs_dbname,
                  tables=_json_table,
                  enums=_json_enum,
                  class_name=make_model_name,
                  get_comments=get_comments)


def save_file(path, data):
    """save_file."""
    with codecs.open(path, 'wb') as fs:
        fs.write(data)


def open_json(filepath):
    """open_json."""
    with codecs.open(filepath, 'r', encoding='utf8') as fs:
        buf = fs.read()

    try:
        return json.loads(buf)
    except UnicodeDecodeError:
        return json.loads(buf)


if __name__ == '__main__':
    options.parse_command_line()
    JSON_DATA = open_json(options.fs_in)

    FILTER_LIST = ['datetime', 'date'] + FLOAT_LIST + \
        STRING_LIST + UINT_LIST + BYTE_LIST

    JSON_ENUM = dict(filter(lambda x: 'type' in x[1] and
                            x[1]['type'] == 'enum' and
                            x[0] not in FILTER_LIST,
                            JSON_DATA.items()))
    JSON_TABLE = dict(filter(lambda x: 'type' in x[1] and
                             x[1]['type'] == 'message' and
                             x[0] not in FILTER_LIST,
                             JSON_DATA.items()))

    JSON_TABLE = init_table_json(JSON_TABLE)

    # if options.fs_mode == 'index':
    #     make_table_init_index_sql(JSON_TABLE)
    # else:

    make_table_init_sql(JSON_TABLE, JSON_ENUM)
    print('sucess')
