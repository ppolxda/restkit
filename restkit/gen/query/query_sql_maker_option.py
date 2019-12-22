# -*- coding: utf-8 -*-
"""
@create: 2017-03-29 18:28:06.

@author: name

@desc: query_sql_maker_option
"""
from __future__ import absolute_import, division, print_function
import os
import re
import glob
import json
import codecs
import pkg_resources
from tornado import template
from tornado.options import options, define

FPAHT_DEFINE = '${fpath}'
FPATH = pkg_resources.resource_filename('restkit.gen.query', 'template')


define("fs_in",
       default='./tools/sql/query/**/*[!_history]*.json',
       type=str, help="glob config path")


define("fs_tmlp",
       default='${fpath}/sql_parse_template.json',
       type=str, help="template file")


define("fs_encoding",
       default='utf8',
       type=str, help="encoding")


define("fs_module_in",
       default='../tools/script/admins.proto.json,../tools/script/users.proto.json',  # noqa
       type=str, help="modules list")


def save_file(path, data):
    """save_file."""
    buf = codecs.open(path, 'wb')
    buf.write(data)
    buf.close()


def fix_str(_val):
    if isinstance(_val, str):
        return _val.replace('"', '\\"')
    else:
        return _val


def json_string_encode(_json):
    if isinstance(_json, list):
        return [
            json_string_encode(val)
            for val in _json
        ]
    elif isinstance(_json, dict):
        for key, val in _json.items():
            _json[key] = json_string_encode(val)
        return _json
    else:
        return fix_str(_json)


def generate_file(file_path, **kwarg):
    """generate_file."""
    global template_obj
    make_data = template_obj.generate(**kwarg)
    save_file(file_path, make_data)


# ----------------------------------------------
#        genconfig
# ----------------------------------------------

UINT_LIAT = ['uint16']
FLOAT_LIST = ['double8_4', 'double16_6', 'double36_14',
              'double16_2', 'double24_8', 'amount_type']
STRING_LIST = ['string4', 'string8', 'string12', 'string16',
               'string24', 'string32', 'string64', 'string128',
               'string256', 'string512', 'string2048', 'jsonString']
BYTE_LIST = ['byte24']


def datatype_change(val):
    if val in ['string', 'bytes', 'date', 'datetime']:
        return val
    elif val == 'bytes' or val in BYTE_LIST:
        return 'bytes'
    elif val in STRING_LIST:
        return 'string'
    elif val in ['int', 'int32', 'int64'] or val in UINT_LIAT:
        return 'int'
    elif val in ['float', 'double'] or val in FLOAT_LIST:
        return 'float'
    elif val in ['json', 'jsonb']:
        return val
    elif len(val) > 4 and (
            val[:4] == 'Enum' or
            val[-4:] == 'Enum'):
        return 'enum'
    else:
        raise Exception('unknow datatype [{}]'.format(val))


def load_config_module(module_path, encoding):
    config_module = {}
    fs_module_in_list = module_path.split(',')
    for fs in fs_module_in_list:
        assert isinstance(fs, str)
        fs = fs.replace('\\', '/')

        with open(fs, 'r', encoding='utf8') as _fs:
            conf_temp = _fs.read()

        _conf_temp = json.loads(conf_temp)

        if not _conf_temp:
            continue

        _conf_temp_list = [i for i in _conf_temp.values()]

        if isinstance(_conf_temp_list[0], list):
            for dbname, tconfigs in _conf_temp.items():

                conf_temp = {}
                for tconfig in tconfigs:
                    msg_type = tconfig.get('msg_type', None)
                    if msg_type != 'TABLE':
                        continue

                    tconfig['fields'] = {
                        config['name'].lower(): config
                        for config in tconfig['fields']
                    }

                    conf_temp[tconfig['table_name'].lower()] = tconfig

                if dbname in config_module:
                    raise TypeError('Duplicate dbname[{}]'.format(dbname))

                config_module[dbname] = conf_temp
        elif isinstance(_conf_temp_list[0], dict):
            conf_temp = {}
            for key, val in _conf_temp.items():
                if 'type' not in val:
                    continue

                if val['type'] == 'message':
                    key = key.lower()

                    if 'options' in val and \
                        'snapshot' in val['options'] and \
                            val['options']['snapshot']:
                        conf_temp['snapshot_' + key] = val

                conf_temp[key] = val

            dbname = fs[fs.rfind('/') + 1:]
            dbname = dbname[:dbname.find('.')]
            config_module[dbname] = conf_temp

    return config_module


def glob_loop(matching):

    config_lists = glob.glob(options.fs_in, recursive=True)

    for file_path in config_lists:
        file_path = file_path.replace('\\', '/')
        # table_name = file_path[file_path.rfind('/') + 1:]
        with codecs.open(file_path, encoding=options.fs_encoding) as fs:
            try:
                file_config = json.loads(fs.read())
            except json.JSONDecodeError:
                raise TypeError('json decode error {}'.format(
                    file_path
                ))

        yield file_path, file_config


def get_dbname(val):
    result = re.match(r'\{hisdbname:(.*?)\}', val)
    if result:
        return result.group(1)
    return val


def loop_generate_file(matching, config_module):

    for file_path, file_config in glob_loop(matching):
        # dirname_data, file_name = os.path.split(file_path)
        config_data = file_config
        if 'group_by' not in config_data:
            config_data['group_by'] = []

        for t in config_data["tables"]:
            if not re.match(r'^(.*?)\.(.*?)$', t['field']):
                raise Exception(
                    'json define error, '
                    'set format "dbname"."tablename" {}'.format(
                        t['field'])
                )

            t['dbname'] = get_dbname(t['field'].split('.')[0])
            t['table_name'] = t['field'].split('.')[1]

        tables = {t['rename']: t for t in config_data["tables"]}

        for field in config_data["fields"]:

            if 'options' not in field:
                field['options'] = {}
            else:
                field['options'] = field['options']

            field_match = re.match(r'^(?P<table>[\w]*?)\.(?P<field>[\w]*?)$',
                                   field['field'], re.IGNORECASE)
            if field_match is None:
                field_match = re.match(
                    r'^(?P<func>SUM)\((?P<table>[\w]*?)\.(?P<field>[\w]*?)\)$',
                    field['field'], re.IGNORECASE)

            if field_match is not None:
                table_name = field_match.groupdict()['table']
                field_name = field_match.groupdict()['field']
                # func_name = field_match.groupdict().get('func', None)
                db_name = tables[table_name]['dbname']
                table_name = tables[table_name]['table_name']
                if table_name == 'history_finish':
                    fields_config = {}
                else:
                    if db_name not in config_module:
                        raise TypeError(
                            '[{}] db [{}] not found'.format(file_path, db_name)
                        )

                    if table_name not in config_module[db_name]:
                        raise TypeError(
                            '[{}] table [{}.{}] not found'.format(
                                file_path, db_name, table_name
                            )
                        )

                    dbconfig = config_module[db_name]
                    fields_config = dbconfig[table_name]['fields']

                fields = {
                    key.lower(): val
                    for key, val in fields_config.items()
                }

                # TAG - define fields
                fields['createtime'] = {
                    "type": "datetime",
                    "id": 99,
                    "comments": "createtime",
                    "options": {
                        "key": "false"
                    }
                }

                fields['updatetime'] = {
                    "type": "datetime",
                    "id": 99,
                    "comments": "updatetime",
                    "options": {
                        "key": "false"
                    }
                }

                fields['htradingday'] = {
                    "type": "datetime",
                    "id": 99,
                    "comments": "htradingday",
                    "options": {
                        "key": "false"
                    }
                }

                fields['snapshottime'] = {
                    "type": "datetime",
                    "id": 99,
                    "comments": "snapshottime",
                    "options": {
                        "key": "false"
                    }
                }

                if field_name not in fields:
                    err = 'can not found field in json {} {} {} [{}][{}]'
                    raise Exception(err.format(db_name, table_name,
                                               field_name, fields.keys(),
                                               file_path))

                field['options']['dataType'] = datatype_change(
                    fields[field_name]['type'])

                if field['options']['dataType'] == 'enum':
                    field['options']["enum"] = '{}_enums.{}'.format(
                        db_name, fields[field_name]['type'] + "Translate")

            # match COUNT func
            elif re.match(r'^(?P<func>COUNT)\((.*?)\)$',
                          field['field'], re.IGNORECASE) is not None:
                field['options']['dataType'] = 'int'

            if 'dataType' not in field['options']:
                raise Exception('dataType not found {} {}'.format(
                    field['field'], file_path))

            elif field['options']['dataType'] == 'enum' and \
                    'enum' not in field['options']:
                raise Exception('enum define not found {} {}'.format(
                    field['field'], file_path))
            # else:
            #     print('(warn): unknow {} {}'.format(
            #         field['field'], file_path))

            # field['options'] = json.dumps(field['options'])

        config_data = json_string_encode(config_data)
        for field in config_data["fields"]:
            field['options'] = json.dumps(field['options'])

        generate_file(file_path, **config_data)


if __name__ == '__main__':
    options.parse_command_line()

    # input_path = options.fs_in

    template_path = options.fs_tmlp
    template_path = template_path.replace(FPAHT_DEFINE, FPATH)
    with open(template_path, 'rb') as fs:
        template_obj = template.Template(fs.read())

    print(template_path)

    _config_module = load_config_module(
        options.fs_module_in, options.fs_encoding)

    print('gen config')

    loop_generate_file(options.fs_in, _config_module)
