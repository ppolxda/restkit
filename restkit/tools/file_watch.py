# -*- coding: utf-8 -*-
"""
@create: 2019-09-24 18:22:05.

@author: name

@desc: file_watch
"""
import os
import re
import six
import csv
import glob
import json
import codecs
import asyncio
import datetime
import shutil
from contextlib import contextmanager


def string2date(val, to_date=True):
    """string2date."""
    if isinstance(val, (datetime.date, datetime.datetime)):
        if not to_date:
            return datetime.datetime(val.year, val.month, val.day)

        if isinstance(val, datetime.datetime):
            return datetime.date(val.year, val.month, val.day)
        return val

    try:
        if to_date:
            return datetime.datetime.strptime(val, '%Y-%m-%d').date()
        else:
            return datetime.datetime.strptime(val, '%Y-%m-%d')
    except ValueError:
        pass
    try:
        if to_date:
            return datetime.datetime.strptime(val, '%Y/%m/%d').date()
        else:
            return datetime.datetime.strptime(val, '%Y/%m/%d')
    except ValueError:
        pass
    try:
        if to_date:
            return datetime.datetime.strptime(val, '%Y%m%d').date()
        else:
            return datetime.datetime.strptime(val, '%Y%m%d')
    except ValueError:  # noqa
        pass


def string2datetime(val):
    """string2datetime."""
    if isinstance(val, (datetime.date, datetime.datetime)):
        if not isinstance(val, datetime.datetime):
            return datetime.datetime(val.year, val.month, val.day)
        return val

    try:
        return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y/%m/%d %H:%M:%S')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y/%m/%dT%H:%M:%S')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y%m%dT%H%M%S')
    except ValueError:  # noqa
        pass
    try:
        return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y/%m/%d %H:%M:%S.%f')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y/%m/%dT%H:%M:%S.%f')
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y%m%dT%H%M%S%f')
    except ValueError:  # noqa
        pass

    return string2date(val, to_date=False)


class FileTask(object):

    RE_DATETIME = re.compile(r'^.+_([0-9]{8}T[0-9]{6})\.csv$')
    RE_DATE = re.compile(r'^.+_([0-9]{8})\.csv$')

    def __init__(self, file_path):
        self.file_path = file_path.replace('\\', '/')

    def get_datetime(self) -> datetime.datetime:
        match = self.RE_DATETIME.match(self.file_path)
        if not match:
            return None

        return string2datetime(match.group(1))

    def get_date(self) -> datetime.datetime:
        match = self.RE_DATE.match(self.file_path)
        if not match:
            return None

        return string2date(match.group(1), False)

    def is_exists(self):
        out_file_path = self.file_path.replace('/watch/', '/pass/')
        return os.path.exists(self.file_path) or os.path.exists(out_file_path)

    @contextmanager
    def load(self, encoding='utf8'):
        with codecs.open(self.file_path, 'r', encoding=encoding) as fs:
            if self.file_path.endswith('.csv'):
                yield csv.reader(fs, delimiter=',', quotechar='\n')
            elif self.file_path.endswith('.json'):
                yield json.loads(fs.read())
            else:
                yield fs.read()

    def dump(self, data, encoding='utf8'):
        if self.file_path.endswith('.csv'):
            if not isinstance(data, six.string_types):
                raise TypeError('csv data invaild')
        elif self.file_path.endswith('.json'):
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            else:
                raise TypeError('csv data invaild')
        else:
            pass

        with codecs.open(self.file_path, 'w', encoding=encoding) as fs:
            fs.write(data)

    def commit(self):
        out_file_path = self.file_path.replace('/watch/', '/pass/')
        shutil.move(self.file_path, out_file_path)

    def error(self, retry=0):
        if retry == 0:
            out_file_path = self.file_path.replace('/watch/', '/error/')
        else:
            out_file_path = self.file_path.replace('/watch/', '/error/')
            out_file_path = out_file_path + '.' + str(retry)

        if os.path.exists(out_file_path):
            self.error(retry + 1)
        else:
            shutil.move(self.file_path, out_file_path)


class FileWatch(object):

    # FILE_FMT = 'feelog_{}.csv'
    FILE_HOUR_FMT = '{prefix}{hour_datetime}{suffix}'
    FILE_DATE_FMT = '{prefix}{date}{suffix}'

    def __init__(self, file_path, prefix='', suffix='.csv', file_fmt=None):
        self.prefix = prefix
        self.suffix = suffix
        self.file_fmt = file_fmt or self.FILE_HOUR_FMT
        self.file_path = file_path
        self.__watch_path = os.path.join(self.file_path, 'watch')
        self.__commit_path = os.path.join(self.file_path, 'pass')
        self.__error_path = os.path.join(self.file_path, 'error')
        self.__glob_regix = os.path.join(
            self.__watch_path, self.prefix + '*.csv'
        )
        self.is_start = False

        try:
            os.makedirs(self.__watch_path)
        except FileExistsError:
            pass

        try:
            os.makedirs(self.__commit_path)
        except FileExistsError:
            pass

        try:
            os.makedirs(self.__error_path)
        except FileExistsError:
            pass

    def __gen_file_path(self, now=None):
        if now is None:
            now = datetime.datetime.now()

        if not isinstance(now, (datetime.datetime, datetime.date)):
            raise TypeError('now invaild')

        return os.path.join(self.__watch_path, self.file_fmt.format(
            prefix=self.prefix,
            suffix=self.suffix,
            hour_datetime=now.strftime('%Y%m%dT%H0000'),
            date=now.strftime('%Y%m%d'),
        ))

    def watch(self):
        config_lists = glob.glob(self.__glob_regix, recursive=True)
        config_lists.sort()

        for file_path in config_lists:
            file_path = file_path.replace('\\', '/')
            # table_name = file_path[file_path.rfind('/') + 1:]

            yield FileTask(file_path)

    def create_task(self, now=None):
        return FileTask(self.__gen_file_path(now))
