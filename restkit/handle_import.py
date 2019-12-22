# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 15:57:29.

@author: name

@desc: handle_import
"""
from __future__ import absolute_import, division, print_function
import re
import os
import sys
import pkgutil
from tornado import template
from restkit.tools.string_unit import is_string

IS_DEBUG = bool(os.environ.get('IS_DEBUG', 'false'))
HANDLER_REGIX = re.compile(r'^.*?_handler$')
COLLECT_FILE_TEMPLATE = template.Template("""
hiddenimports = [{% for module in collect_modules%}
    '{{module}}',{%end%}
]


def import_modules():
    for module in hiddenimports:
        __import__(module)
""")


COLLECT_FILE2_TEMPLATE = template.Template("""
{% for module in collect_modules%}
from {{module[:module.rfind('.')]}} import {{module[module.rfind('.') + 1:]}} as chandler_{{collect_modules.index(module)}}  # noqa{%end%}


__all__ = [{% for module in collect_modules%}
    'chandler_{{collect_modules.index(module)}}',{%end%}
]
""")


COLLECT_HOOKS_FILE_TEMPLATE = template.Template("""
from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('{{module_name}}')
""")


def walk_packages(path=None, prefix='', onerror=None):
    # def seen(p, m={{}}):
    #     if p in m:
    #         return True
    #     m[p] = True

    for importer, name, ispkg in pkgutil.iter_modules(path, prefix):
        if not name.startswith(prefix):  # Added
            name = prefix + name  # Added
        yield importer, name, ispkg


def collect_local_modules(module_name, hooks_module='.hooks'):
    """collect_local_modules."""

    if getattr(sys, 'frozen', False) or not IS_DEBUG:
        return

    def is_invaild_module_name(name):
        return not is_string(name) or \
            re.match(r'^(\.[a-zA-Z0-9_-]{1,}){1,}$', name) is None

    if is_invaild_module_name(module_name):
        raise TypeError('module_name invaild')

    if is_invaild_module_name(hooks_module):
        raise TypeError('module_name invaild')

    module_name = module_name[1:]
    module_path = module_name.replace('.', '/')
    module_collect_path = module_name.replace('.', '/') + '/collect_modules.py'
    # module_collect_name = module_name + '.collect_modules'
    # hooks_path = '.' + hooks_module.replace('.', '/')
    # hooks_file = '{0}/hook-{1}.py'.format(hooks_path, module_name)

    modules = [x for x in __collect_handler_modules(module_path)]
    _file = open(module_collect_path, 'wb')
    _file.write(COLLECT_FILE2_TEMPLATE.generate(collect_modules=modules))
    _file.close()


def __get_files(root_dir, file_types, filters):
    """__get_files.

    file_types = ['.css', '.js', '.htm']
    filters = ['', '.min.', 'sweet-alert']
    """

    def is_vaild_file(filename, file_types):
        if not file_types:
            return False
        for x in file_types:
            if filename.endswith(x):
                return True
        return False

    def is_filter_file(file_path, filters):
        if not filters:
            return False
        for y in filters:
            if file_path.find(y) > 0:
                return True
        return False

    for root, _, files in os.walk(root_dir):
        for filename in files:
            file_path = os.path.join(root, filename)

            if not is_vaild_file(filename, file_types):
                continue

            if is_filter_file(file_path, filters):
                continue

            yield (file_path, filename, filename[filename.rfind('.'):])


def __collect_handler_modules(collect_path):
    collect_path = collect_path.replace('\\', '/')
    relative_path = collect_path.replace('/', '.')

    for file_data in __get_files(collect_path, ['.py'], ['__init__.py']):
        file_path = file_data[0].replace('\\', '/').replace(collect_path, '')
        file_path = file_path[:-3].replace('/', '.')

        module_name = relative_path + file_path
        if re.match(HANDLER_REGIX, module_name) is None:
            continue

        yield module_name
