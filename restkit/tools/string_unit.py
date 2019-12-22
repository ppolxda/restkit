# -*- coding: utf-8 -*-
"""
Created on 2019-08-23 18:01:15.

@author: name
"""
from __future__ import absolute_import, division, print_function
import re
import sys
import string
import datetime
import random
# import xmltodict


class FeildInVaild(Exception):
    pass


def string2datetime(val):
    """string2datetime."""
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
    except ValueError:
        raise


def string2date(val, to_date=True):
    """string2date."""
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


if sys.version_info[0] == 3:
    basestring = str


def is_string(val):
    return isinstance(val, basestring)


def is_float(val):
    try:
        float(val)
    except ValueError:
        return False
    return True


def is_int(val):
    try:
        int(val)
    except ValueError:
        return False
    return True


# def is_date(val):
#     if not is_string(val):
#         return False
#     return re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', val) is not None

def is_date(val):
    if not is_string(val):
        return False
    return re.match(r'[0-9]{4}[0-9]{2}[0-9]{2}', val) is not None

# def is_datetime(val):
#     if not is_string(val):
#         return False
#     return re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}', val) is not None  # noqa


def is_datetime(val):
    if not is_string(val):
        return False
    return re.match(r'[0-9]{4}[0-9]{2}[0-9]{2}T[0-9]{2}[0-9]{2}[0-9]{2}', val) is not None  # noqa


def is_boolean(val):
    return val is True or val is False


LOGINCODE_REGIX = re.compile(r'^([\w@\+\._-]{1,32})$')
PASSWORD_REGIX = re.compile(r'^([\w' + string.punctuation + ']{6,128})$')
NUMBER_REGIX = re.compile(r'^[0-9]{1,}$')
EMAIL_REGIS = re.compile(
    r'^([A-Za-z0-9\.\+_-]+)@([A-Za-z0-9\._-]+\.[a-zA-Z]*)$')
TELCODE_REGIS = re.compile(r'^[\+]{1}[0-9]{1,}$')


def is_vaild_telcode(data):
    return re.match(TELCODE_REGIS, data) is not None


def is_vaild_logincode(data):
    return re.match(LOGINCODE_REGIX, data) is not None


def is_vaild_password(data):
    return re.match(PASSWORD_REGIX, data) is not None


def is_vaild_number(data):
    return re.match(NUMBER_REGIX, data) is not None


def is_vaild_email(data):
    return re.match(EMAIL_REGIS, data) is not None


is_number = is_vaild_number  # noqa
is_email = is_vaild_email  # noqa


def encode_email(email):
    email_groups = re.match(EMAIL_REGIS, email)
    if email_groups is None:
        return None

    mail = email_groups.group(1)
    size = len(mail)
    if size <= 2:
        return email
    elif size == 3:
        return mail[0] + '*' + mail[2] + '@' + email_groups.group(2)
    elif size == 4:
        return mail[0:1] + '*' + mail[2:4] + '@' + email_groups.group(2)
    elif size == 5:
        return mail[0:2] + '*' + mail[3:6] + '@' + email_groups.group(2)
    elif size == 6:
        return mail[0:2] + '**' + mail[4:7] + '@' + email_groups.group(2)
    elif size == 7:
        return mail[0:2] + '**' + mail[4:8] + '@' + email_groups.group(2)
    elif size == 8:
        return mail[0:2] + '***' + mail[5:10] + '@' + email_groups.group(2)
    elif size == 9:
        return mail[0:3] + '***' + mail[6:9] + '@' + email_groups.group(2)
    elif size == 10:
        return mail[0:3] + '****' + mail[7:10] + '@' + email_groups.group(2)
    elif size == 11:
        return mail[0:3] + '****' + mail[7:11] + '@' + email_groups.group(2)
    else:
        temp = mail[0:4]
        temp = '*' * (len(mail) - 8)
        return temp + mail[-4:] + '@' + email_groups.group(2)
    return email


def encode_string(val):
    if val:
        size = len(val)
        if size <= 2:
            return val
        elif size == 3:
            return val[0] + '***' + val[2]
        elif size == 4:
            return val[0:1] + '***' + val[2:4]
        elif size == 5:
            return val[0:2] + '***' + val[3:6]
        elif size == 6:
            return val[0:2] + '***' + val[4:7]
        elif size == 7:
            return val[0:2] + '***' + val[4:8]
        elif size == 8:
            return val[0:2] + '***' + val[5:10]
        elif size == 9:
            return val[0:3] + '***' + val[6:9]
        elif size == 10:
            return val[0:3] + '***' + val[7:10]
        elif size == 11:
            return val[0:3] + '***' + val[7:11]
        else:
            temp = val[0:4]
            temp = '*' * (len(val) - 8)
            return temp + val[-4:]
        return string
    return None


if sys.version_info > (3,):
    long = int
    unicode = str
    boolean = bool
    # str = bytes


def convert(value, data_type):
    """ Convert / Cast function """
    if value is None:
        return value
    elif issubclass(data_type, str) and \
            not (value.upper() in ['FALSE', 'TRUE']):
        return value
    elif issubclass(data_type, unicode):
        return unicode(value)
    elif issubclass(data_type, int):
        return int(value)
    elif issubclass(data_type, long):
        return long(value)
    elif issubclass(data_type, float):
        return float(value)
    elif issubclass(data_type, boolean) and \
            (value.upper() in ['FALSE', 'TRUE']):
        if str(value).upper() == 'TRUE':
            return True
        elif str(value).upper() == 'FALSE':
            return False
    else:
        return value


def random_number(size=6):
    return ''.join([random.choice(string.digits) for i in range(size)])


def decode_str(val):
    """decode_str."""
    try:
        return unicode(val)
    except Exception:
        pass
    try:
        return val.decode()
    except Exception:
        pass
    try:
        return val.decode('utf8')
    except Exception:
        pass
    try:
        return val.decode('gbk')
    except Exception:
        pass
    try:
        return val.decode('gb2312')
    except Exception:
        raise


def encode_utf8(val):
    """encode_utf8."""
    try:
        return val.encode('utf8')
    except Exception:
        pass
    try:
        return val.decode('gbk').encode('utf8')
    except Exception:
        pass
    try:
        return val.decode('gb2312').encode('utf8')
    except Exception:
        raise
