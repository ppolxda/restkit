# -*- coding: utf-8 -*-
"""
@create: 2017-03-29 18:28:06.

@author: name

@desc: query_sql_maker
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
from .query_tools import sql_parse

FPAHT_DEFINE = '${fpath}'
FPATH = pkg_resources.resource_filename('restkit.gen.query', '')

define("fs_in",
       default='./tools/sql/query/**/*[!_history]*.json',
       type=str, help="glob path")


define("fs_tmlp",
       default='${fpath}/template/sql_query_temlate.tmlp',
       type=str, help="template file")


define("fs_encoding",
       default='utf8',
       type=str, help="fs_encoding")


define("pkgname",
       default=None,
       type=str, help="pkgname")


def save_file(path, data):
    """save_file."""
    buf = codecs.open(path, 'wb')
    buf.write(data)
    buf.close()


def generate_file(file_path, **kwarg):
    """generate_file."""
    make_data = template_obj.generate(**kwarg)
    save_file(file_path, make_data)


# ----------------------------------------------
#        gen config
# ----------------------------------------------

def escape_python(val):
    if "'" in val:
        val = val.replace("'", "\\'")
    return val


def long_string_fromat(val, maxlen=30, pos=0):
    if len(val) < maxlen:
        return "'{}'".format(val)

    # escape
    val = escape_python(val)

    def split_str(_val, _maxlen):
        while len(_val) >= _maxlen:
            yield "'{}'".format(_val[:_maxlen])
            _val = _val[_maxlen:]

        if _val:
            yield "'{}'".format(_val)

    pos_spen = '\n' + ' ' * pos
    strlist = list(split_str(val, maxlen))
    return '(' + pos_spen.join(strlist) + ')'


def dbname_replace(val):
    return re.sub(r'\{hisdbname:(.*?)\}', r'history_\1', val)


if __name__ == '__main__':
    options.parse_command_line()

    pkgname = options.pkgname
    template_path = options.fs_tmlp
    template_path = template_path.replace(FPAHT_DEFINE, FPATH)
    with codecs.open(template_path, 'rb') as fs:
        template_obj = template.Template(fs.read())
    print(template_path)

    # ----------------------------------------------
    #        common
    # ----------------------------------------------

    # open file
    print(options.fs_in)
    config_lists = glob.glob(options.fs_in, recursive=True)
    # config_lists = file_tools.open_json_from_path(options.fs_in, True)
    # {'fname': {'path': '', 'config': ''}}
    print('gen config')

    for file_path in config_lists:
        file_path = file_path.replace('\\', '/')
        table_name = file_path[file_path.rfind('/') + 1:]
        with codecs.open(file_path, encoding=options.fs_encoding) as fs:
            file_config = json.loads(fs.read())

        # for line in file_config['fields']:
        #     # escape "'"
        #     line['field'] = line['field'].replace("'", "\\'")

        for line in file_config['tables']:
            # rename hisdb table {hisdbname:trade} -> {hisdbname}
            line['field'] = dbname_replace(line['field'])

        dirname_data, file_name = os.path.split(file_path)
        config_data = file_config
        config_data['query_name'] = table_name
        config_data['query_sql'] = sql_parse.json2query_sql(config_data, False, True)  # noqa
        config_data['long_string_fromat'] = long_string_fromat
        config_data['escape_python'] = escape_python
        config_data['pkgname'] = pkgname

        generate_file(
            file_path[:file_path.rfind('.')] +
            '_query_sql.py', **config_data
        )
