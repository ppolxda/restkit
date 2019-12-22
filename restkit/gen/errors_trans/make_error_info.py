# -*- coding: utf-8 -*-
"""
Created on 2019-10-11 19:30:45.

@author: name
"""
import re
import os
import csv
import codecs
import pkg_resources
from tornado.template import Template
from tornado.options import options, define

FPAHT_DEFINE = '${fpath}'
FPATH = pkg_resources.resource_filename('restkit.gen.errors_trans', '')
DEFAULT_CSV = '${fpath}/error_info.csv'


define('fs_in', '', str)
define('fs_out', './tools/error_info.py', str)
define('fs_tmpl', '${fpath}/error_info.jinja', str)
define('service', 'test', str)


def open_file(path):
    """open_file."""
    return codecs.open(path, encoding='utf8').read()


def open_csv(path):
    """open_csv."""
    _lines = []
    with codecs.open(path, encoding='utf8') as fs:
        for line in csv.reader(fs):
            if len(line) == 3:
                _lines.append(line)

    return _lines


def delete_space_line(path):
    """delete_space_line."""
    new_lines = ''
    with codecs.open(path, 'r', encoding='utf8') as fs:
        sub_status = False
        for line in fs.readlines():
            if line.find('Array Begin') != -1:
                sub_status = True
            if line.find('Array End') != -1:
                sub_status = False

            if sub_status:
                if re.search('[0-9a-zA-Z]{1,}', line):
                    new_lines += line
            else:
                new_lines += line

    with codecs.open(path, 'w', encoding='utf8') as fs:
        fs.write(new_lines)


if __name__ == '__main__':
    options.parse_command_line()
    default_csv = DEFAULT_CSV.replace(FPAHT_DEFINE, FPATH)
    options.fs_in = options.fs_in.replace(FPAHT_DEFINE, FPATH)
    options.fs_tmpl = options.fs_tmpl.replace(FPAHT_DEFINE, FPATH)
    error_data = open_csv(options.fs_in) if options.fs_in else None
    default_error_data = open_csv(default_csv)
    error_jinja = open_file(options.fs_tmpl)

    default_error_index = [
        i[0]
        for i in default_error_data
    ]

    default_error_enum = [
        i[1]
        for i in default_error_data
    ]

    if error_data:
        if options.fs_tmpl.endswith('sub.jinja'):
            for i in error_data:
                if int(i[0]) <= 200:
                    raise TypeError('csv index must > 200 [{}]'.format(i))

                if i[0] in default_error_index:
                    raise TypeError('csv index duplicate [{}]'.format(i))

                if i[1] in default_error_enum:
                    raise TypeError('csv enum duplicate [{}]'.format(i))

        error_data = error_data
    else:
        error_data = []

    template = Template(error_jinja)
    make_data = template.generate(**{
        'service': options.service,
        'error_infos': error_data
    })
    with codecs.open(options.fs_out, 'w', encoding='utf8') as fs:
        fs.write(make_data.decode('utf8'))

    delete_space_line(options.fs_out)
    print('sucess')
