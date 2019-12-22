# -*- coding: utf-8 -*-
"""
@create: 2017-10-13 11:10:34.

@author: name

@desc: api_template_maker
"""
import re
import os
import json
import time
import codecs
import random
import hashlib
import datetime
from tornado import gen
from tornado import ioloop
from tornado import template
from tornado import httpclient
from tornado.options import options, define

FPAHT_DEFINE = '${fpath}'
FPATH = os.path.abspath(os.path.dirname(__file__))

# try:
#     from functools import reduce
# except ImportError:
#     pass

define('fs_in', 'http://192.168.1.24:10000/devel/config_api_json', str)
define('fs_out', './out/administrate.sql', str)
define('fs_tmpl', './template/init_sql/create_table_index_tmpl.sql', str)
define('fs_kwargs', '', str)
define('service_name', 'service_name', str)
define('concat', False, bool)


INT_LIST = ['int32', 'int64', 'uint32', 'uint64', 'uint16']
FLOAT_LIST = ['float', 'double'] + ['double8_4', 'double16_6', 'double36_14',
                                    'double16_2', 'double24_8', 'amount_type']
STRING_LIST = ['string', 'string4', 'string8', 'string12', 'string16',
               'string24', 'string32', 'string64', 'string128',
               'string256', 'string512']
BYTE_LIST = ['bytes', 'byte24']
JSON_LIST = ['jsonString', 'jsonb', 'json']
DATETIME_LIST = ['date', 'datetime']


def datatype_change(field):
    val = field['type']
    if val in BYTE_LIST:
        return 'string'
    elif val in DATETIME_LIST:
        return 'Date'
    elif val in STRING_LIST:
        return 'string'
    elif val in INT_LIST:
        return 'number'
    elif val in FLOAT_LIST:
        return 'number'
    elif val in JSON_LIST:
        return 'any'
    elif val == 'list_int32':
        return 'number[]'
    elif val == 'list_string':
        return 'string[]'
    elif val == 'list_class':
        return 'Array<any>'
    elif len(val) > 4 and (
            val[:4] == 'Enum' or
            val[-4:] == 'Enum'):
        return field['dbname'] + '_enums.' + val
    elif len(val) > 5 and (
            val[:5] == 'Field' or
            val[-5:] == 'Field'):
        return 'any'
    else:
        raise Exception('unknow datatype [{}]'.format(val))


def options_concat(options_filed):
    assert isinstance(options_filed, dict)
    result = ''
    for key, val in options_filed.items():
        if key in ['enum', 'func']:
            result += ', {}: {}'.format(key, val)
        else:
            result += ', {}: \'{}\''.format(key, val)
    return result


def underline_to_camel(underline_format):
    '''underline_to_camel.'''
    camel_format = ''
    if isinstance(underline_format, str):
        for _s_ in underline_format.split('_'):
            if camel_format == '':
                camel_format += _s_.capitalize()
            elif _s_ == 'id':
                camel_format += 'ID'
            else:
                camel_format += _s_.capitalize()

    return camel_format


def make_model_name(table, space_characters='_'):
    model = re.sub(r'[^\w]+', '', table)
    model_name = ''.join(sub.title()
                         for sub in model.split(space_characters))
    if not model_name[0].isalpha():
        model_name = 'T' + model_name
    return model_name


def generate_file(tmpl_path, file_path, concat, **kwargs):
    """generate_file."""
    # template_loader = template.Loader(options.fs_tmpl)
    tmpl_path = tmpl_path.replace(FPAHT_DEFINE, FPATH)
    with codecs.open(tmpl_path, 'rb') as fs:
        tmpl = fs.read()

    make_data = template.Template(tmpl).generate(**kwargs)
    if concat:
        mode = 'ab+'
    else:
        mode = 'wb'

    with codecs.open(file_path, mode) as fs:
        fs.write(make_data)

    return make_data


def init_table_json(_json_table):
    assert isinstance(_json_table, dict)

    for tables in _json_table.values():
        if 'nested' not in tables:
            tables['nested'] = {}

        for field in tables['fields'].values():
            if 'options' not in field:
                field['options'] = {}

            if 'default' not in field['options']:
                field['options']['default'] = None

            if field['options']['default'] == '"now"' and \
                    field['type'] == 'datetime':
                field['options']['default'] = 'CURRENT_TIMESTAMP'

            if field['options']['default'] == '"now"' and \
                    field['type'] == 'date':
                field['options']['default'] = ''

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


def dict2json_string(data, indent=None):
    data = json.dumps(data, indent=indent)
    data = data.replace('\n', '\\n')
    data = data.replace('"', '\\"')
    return data


def yapi_subtopic(api_config):
    assert isinstance(api_config, dict)
    reuslt = {}
    for key, val in api_config.items():
        path = '_'.join(val['rest_path'].split('/')[:-1])[1:].strip()
        if path not in reuslt:
            reuslt[path] = {}
        reuslt[path][key] = val
    return reuslt


def yapi_field(key, val):
    # {
    #     "type": "boolean",
    #     "default": true
    # }
    if val['type'] == 'bytes' or val['type'] in BYTE_LIST:
        result = {
            "type": "string",
            "description": val.get('comment', None),
            "minLength": val['options'].get('minlen', None)
            if 'options' in val else None,
            "maxLength": val['options'].get('maxlen', None)
            if 'options' in val else None
        }

    elif val['type'] in ['date', 'datetime']:
        result = {
            "type": "string",
            "description": val.get('comment', None),
            "minLength": val['options'].get('minlen', None)
            if 'options' in val else None,
            "maxLength": val['options'].get('maxlen', None)
            if 'options' in val else None,
            "format": "date-time" if val['type'] == 'date' else "date"
        }

    elif val['type'] in STRING_LIST or val['type'] in ['string']:
        result = {
            "type": "string",
            "description": val.get('comment', None),
            "minLength": val['options'].get('minlen', None)
            if 'options' in val else None,
            "maxLength": val['options'].get('maxlen', None)
            if 'options' in val else None
        }

    elif val['type'] in ['int', 'int32', 'int64'] or val['type'] in UINT_LIAT:
        result = {
            "type": "integer",
            "description": val.get('comment', None),
            "minimum": val['options'].get('minval', None)
            if 'options' in val else None,
            "maximum": val['options'].get('maxval', None)
            if 'options' in val else None
        }

    elif val['type'] in ['float', 'double'] or val['type'] in FLOAT_LIST:
        result = {
            "type": "number",
            "description": val.get('comment', None),
            "minimum": val['options'].get('minval', None)
            if 'options' in val else None,
            "maximum": val['options'].get('maxval', None)
            if 'options' in val else None
        }
    elif val['type'] == 'list_int32':
        result = {
            "type": "array",
            "items": {
                "type": "integer",
                "description": val.get('comment', None),
                "minimum": val['options'].get('minval', None)
                if 'options' in val else None,
                "maximum": val['options'].get('maxval', None)
                if 'options' in val else None
            }
        }
    elif val['type'] == 'list_string':
        result = {
            "type": "array",
            "items": {
                "type": "string",
                "description": val.get('comment', None),
                "minLength": val['options'].get('minlen', None)
                if 'options' in val else None,
                "maxLength": val['options'].get('maxlen', None)
                if 'options' in val else None
            }
        }
    elif len(val['type']) > 4 and (
            val['type'][:4] == 'Enum' or
            val['type'][-4:] == 'Enum'):
        result = {
            "type": "integer",
            "description": val.get('comment', None),
            "minimum": val['options'].get('minval', None)
            if 'options' in val else None,
            "maximum": val['options'].get('maxval', None)
            if 'options' in val else None
        }
    else:
        raise Exception('unknow datatype [{}]'.format(val))

    for i in list(result.keys()):
        if result[i] is None:
            del result[i]

        if result['type'] == "array":

            for i in list(result['items'].keys()):
                if result['items'][i] is None:
                    del result['items'][i]

    return result


def make_table_init_sql(_json_table):
    """make_table_init_sql."""
    assert isinstance(_json_table, dict)
    fs_kwargs = options.fs_kwargs.split(',')
    fs_kwargs = {
        i.split(':')[0].strip():
        i.split(':')[1].strip()
        for i in fs_kwargs
        if i.find(':') >= 0}

    generate_file(
        options.fs_tmpl,
        options.fs_out,
        options.concat,
        service_name=options.service_name,
        kwargs=fs_kwargs,
        api_config=_json_table,
        class_name=make_model_name,
        underline_to_camel=underline_to_camel,
        options_concat=options_concat,
        datatype_change=datatype_change,
        dict2json_string=dict2json_string,
        yapi_field=yapi_field,
        yapi_subtopic=yapi_subtopic,
        time=time,
        json=json,
        random=random,
        hashlib=hashlib,
        datetime=datetime.datetime
    )


@gen.coroutine
def main():
    http_client = httpclient.AsyncHTTPClient()
    result = yield http_client.fetch(options.fs_in, method='GET')
    result = json.loads(result.body)

    # result = init_table_json(result)
    make_table_init_sql(result)


if __name__ == '__main__':
    options.parse_command_line()
    ioloop.IOLoop.instance().run_sync(main)

    # if options.fs_mode == 'index':
    #     make_table_init_index_sql(JSON_TABLE)
    # else:

    print('sucess')
