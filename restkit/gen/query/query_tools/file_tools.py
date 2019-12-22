# -*- coding: utf-8 -*-
"""
@create: 2017-03-29 18:36:33.

@author: name

@desc: file_tools
"""
import os
import json
import shutil
import codecs

workpath = os.getcwd() + '/'
dirname = os.path.dirname
split = os.path.split

# ----------------------------------------------
#        file path
# ----------------------------------------------

exists = os.path.exists
copyfile = shutil.copyfile


def save_file(path, data):
    """save_file."""
    buf = codecs.open(path, 'wb')
    buf.write(data)
    buf.close()


def mdir(output_path):
    """mdir."""
    try:
        os.makedirs(output_path)
    except Exception:
        pass


def get_files(root_dir, file_types, filters, include_sub_dir=False):
    """get_files.

    file_types = ['.css', '.js', '.htm']
    filters = ['', '.min.', 'sweet-alert']
    """
    result = {}

    def is_vaild_file(filename, file_types):
        """is_vaild_file."""
        if not file_types:
            return False
        for p in file_types:
            if filename.endswith(p):
                return True
        return False

    def is_filter_file(file_path, filters):
        """is_filter_file."""
        if not filters:
            return False
        for p in filters:
            if file_path.find(p) > 0:
                return True
        return False

    for root, dirs, files in os.walk(root_dir):  # nowa
        for filename in files:
            file_path = os.path.join(root, filename)
            if not is_vaild_file(filename, file_types):
                continue
            if is_filter_file(file_path, filters):
                continue

            filetype = filename[filename.find('.'):]
            if filetype not in result:
                result[filetype] = []
            result[filetype].append((file_path, filename))

        # include_sub_dir
        if include_sub_dir:
            for _dir in dirs:
                sub_result = get_files(
                    root + '/' + _dir, file_types, filters, include_sub_dir)
                if sub_result:
                    for filetype in sub_result:
                        if filetype not in result:
                            result[filetype] = []
                        result[filetype] += sub_result[filetype]

    return result


# ----------------------------------------------
#        about json
# ----------------------------------------------

def open_json(filepath):
    """open_json."""
    try:
        buf = codecs.open(filepath, 'r', encoding='utf8').read()
    except Exception:
        buf = codecs.open(filepath, 'r', encoding='gbk').read()
    return json.loads(buf)


def open_json_from_path(path, include_sub_dir=False):
    """open_json_from_path.

    output = {
        'mdbs.json': {
            'path': './input/mdbs/mdbs.json',
            'config': {}
        }
    }
    """
    json_file_list = get_files(path, ['.json'], [], include_sub_dir)
    if len(json_file_list) <= 0:
        return json_file_list
    assert '.json' in json_file_list
    return {json_file[1]: {
        "path": json_file[0],
        "config": open_json(json_file[0])}
        for json_file in json_file_list['.json']}
