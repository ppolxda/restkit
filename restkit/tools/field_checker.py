# -*- coding: utf-8 -*-
"""
@create: 2017-03-30 04:06:01.

@author: name

@desc: field_checker
"""
import os
import re
import sys
import six
import json
import decimal
import datetime
from restkit.tools.string_unit import is_string
from restkit.tools.string_unit import is_int
from restkit.tools.string_unit import is_float
from restkit.tools.string_unit import is_datetime
from restkit.tools.string_unit import is_date
from restkit.tools.string_unit import is_boolean
from restkit.tools.string_unit import FeildInVaild
# from tools.error_info import _
# from tools.error_info import error_info


def _(val):
    return val


INT_LIST = ['int32', 'int64', 'uint32', 'uint64', 'uint16']
FLOAT_LIST = ['float', 'double'] + ['double8_4', 'double16_6', 'double36_14',
                                    'double16_2', 'double24_8', 'amount_type']
STRING_LIST = ['string', 'string4', 'string8', 'string12', 'string16',
               'string24', 'string32', 'string64', 'string128',
               'string256', 'string512']
BYTE_LIST = ['bytes', 'byte24']
JSON_LIST = ['jsonString', 'jsonb', 'json']
DEFDATE = datetime.date(1900, 1, 1)
DEFDATETIME = datetime.datetime(1900, 1, 1)
IS_DEBUG = bool(os.environ.get('IS_DEBUG', 'false'))


def parames_config_dict(field_type, comment, default='',
                        update='false', maxlen=None,
                        minlen=None, maxval=None,
                        minval=None, memo=None):
    return {
        'type': field_type,
        'default': default,
        'comment': comment,
        'options': {
            'update': update,
            'maxlen': maxlen,
            'minlen': minlen,
            'maxval': maxval,
            'minval': minval,
            'memo': memo,
        },
    }


def parames_config(field, default=None, memo=None):
    result = {
        'default': default,
        'type': field['type'],
        'dbname': field['dbname'] if 'dbname' in field else '',
        'comment': field['comment'],
        'options': field['options']
    }
    if memo:
        result['options']['memo'] = memo
    return result


class FeildOption(object):

    class Options(object):

        def __init__(self, update='false', maxlen=None,
                     minlen=None, maxval=None, minval=None,
                     regix=None, memo=None):
            self.update = update
            self.maxlen = maxlen
            self.minlen = minlen
            self.maxval = maxval
            self.minval = minval
            self.regix = regix
            self.memo = memo

        def to_dict(self):
            return {
                'update': self.update,
                'maxlen': self.maxlen,
                'minlen': self.minlen,
                'maxval': self.maxval,
                'minval': self.minval,
                'regix': self.regix,
                'memo': self.memo,
            }

        def __str__(self):
            return json.dumps(self.to_dict())

        def __repr__(self):
            return self.__str__()

    def __init__(self, field_type, comment, default=None,
                 update='false', maxlen=None,
                 minlen=None, maxval=None, minval=None,
                 dbname='', regix=None, optional=True,
                 memo=None):
        self.type = field_type
        self.comment = comment
        self.default = default
        self.dbname = dbname
        self.optional = optional
        self.options = self.Options(update, maxlen,
                                    minlen, maxval, minval,
                                    regix, memo)

    @staticmethod
    def from_dict(**option):
        return FeildOption(**option)

    def to_dict(self):
        return {
            'default': self.default,
            'type': self.type,
            'dbname': self.dbname,
            'comment': self.comment,
            'optional': self.optional,
            'options': self.options.to_dict()
        }

    def __str__(self):
        return json.dumps(self.to_dict())

    def __repr__(self):
        return self.__str__()


def convert_type(key, value, ftype, encoding='utf8'):
    """ Convert / Cast function """
    # assert isinstance(value, six.string_types)
    assert isinstance(ftype, six.string_types)
    assert isinstance(encoding, six.string_types)

    try:
        if value is None:
            return value

        elif ftype in ['bytes'] or \
                ftype in BYTE_LIST or \
                ftype == 'datetime' or \
                ftype == 'date':
            if isinstance(value, six.string_types):
                value = value.encode(encoding)
            return value

        elif ftype in INT_LIST:
            return int(value)

        elif ftype in FLOAT_LIST:
            return decimal.Decimal(value)

        elif ftype == 'boolean':
            if value.upper() == 'TRUE':
                return True
            else:
                return False
        else:
            return value
    except ValueError:
        raise FeildInVaild(_('Request parames Invaild[{}]').format(key))


class FeildCheck(object):

    fields = {}
    field_keys = set(fields.keys())
    field_lowers = dict()
    field_update_keys = set(key for key, val in fields.items()
                            if val['options']['update'] == 'true')
    field_primary_keys = set(key for key, val in fields.items()
                             if val['options']['key'] == 'true')

    @staticmethod
    def field_req_checks(inputs, options):
        # req_keys = set(key for key, val in options.items()
        #                if isinstance(val, FeildOption) and
        #                not val.optional)

        for key, val in options.items():
            if isinstance(val, FeildOption) and \
                    (not val.optional) and \
                    key not in inputs:
                raise FeildInVaild(
                    _('Request fields missing[{}]').format(key))

    @staticmethod
    def field_checks(inputs, options, check_req=False):
        assert isinstance(inputs, dict)
        assert isinstance(options, dict)
        if check_req:
            FeildCheck.field_req_checks(inputs, options)

        for key, val in inputs.items():
            option = options.get(key, None)
            if option is None:
                raise FeildInVaild(_('Request fields missing[{}]').format(key))

            if isinstance(option, FeildOption):
                pass
            elif isinstance(option, dict):
                option = FeildOption.from_dict(**option)
            else:
                raise FeildInVaild(_('Request config error[{}]').format(key))

            FeildCheck.field_check(key, val, option.type,
                                   option.options.to_dict())

    @classmethod
    def field_defval(cls, key, ftype, default):
        if default is not None:
            return default

        if ftype in JSON_LIST:
            return {}

        elif ftype in STRING_LIST:
            return ''

        elif ftype in BYTE_LIST:
            return b''

        elif ftype in INT_LIST:
            return 0

        elif ftype in FLOAT_LIST:
            return decimal.Decimal('0.0')

        elif ftype == 'datetime':
            return DEFDATETIME

        elif ftype == 'date':
            return DEFDATE

        elif ftype == 'boolean':
            return False

        elif ftype == 'class':
            return None

        elif len(ftype) > 5 and (
                ftype[:5] == 'Field' or
                ftype[-5:] == 'Field'):
            return {}

        elif len(ftype) > 4 and (
                ftype[:4] == 'Enum' or
                ftype[-4:] == 'Enum'):
            return 0

        else:
            raise FeildInVaild(_('Field type error[{}]').format(key))

    @staticmethod
    def field_check(key, val, ftype, option, check_array=True):
        args = (option, key, val)

        if check_array and option.get('is_array', False):
            if not isinstance(field_dict[key], (list, set)):
                raise FeildInVaild(
                    _('Field Invaild, type error[array][{}]').format(key))  # noqa

            for _val in field_dict[key]:
                FeildCheck.field_check(key, _val, ftype, option, False)

        elif ftype in JSON_LIST:
            FeildCheck.field_json(*args)

        elif ftype in STRING_LIST:
            FeildCheck.field_string(*args)

        elif ftype in BYTE_LIST:
            FeildCheck.field_bytes(*args)

        elif ftype in INT_LIST:
            FeildCheck.field_int(*args)

        elif ftype in FLOAT_LIST:
            FeildCheck.field_float(*args)

        elif ftype == 'datetime':
            FeildCheck.field_datetime(*args)

        elif ftype == 'date':
            FeildCheck.field_date(*args)

        elif ftype == 'boolean':
            FeildCheck.field_boolean(*args)

        elif ftype == 'class':
            FeildCheck.field_class(*args)

        # elif len(ftype) > 4 and (
        #         ftype[:4] == 'Enum' or
        #         ftype[-4:] == 'Enum'):
        #     FeildCheck.field_enum(
        #         ftype,
        #         option,
        #         key, val
        #     )
        else:
            raise FeildInVaild(_('Field type error[{}]').format(key))

    @staticmethod
    def field_int(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not isinstance(val, int):
            raise FeildInVaild(
                _('Field Invaild, type error[int][{}]').format(key))

        # if not is_int(val):
        #     raise FeildInVaild(
        #         _('Field Invaild, type error[int][{}]').format(key))

        minval = options.get('minval', None)
        maxval = options.get('maxval', None)

        val = int(val)
        if minval is not None and val < int(minval):
            raise FeildInVaild(
                _('Field Invaild, input range error[{}][min={}]').format(
                    key, minval))

        if maxval is not None and val > int(maxval):
            raise FeildInVaild(
                _('Field Invaild, input range error[{}][max={}]').format(
                    key, maxval))

    @staticmethod
    def field_float(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not isinstance(val, (float, int, decimal.Decimal)):
            raise FeildInVaild(
                _('Field Invaild, type error[float][{}]').format(key))

        # if not is_float(val):
        #     raise FeildInVaild(
        #         _('Field Invaild, type error[float][{}]').format(key))

        minval = options.get('minval', None)
        maxval = options.get('maxval', None)

        val = float(val)
        if minval is not None and val < float(minval):
            raise FeildInVaild(
                _('Field Invaild, input range error[{}][min={}]').format(
                    key, minval))

        if maxval is not None and val > float(maxval):
            raise FeildInVaild(
                _('Field Invaild, input range error[{}][max={}]').format(
                    key, maxval))

    @staticmethod
    def field_class(options, key, val):
        if not isinstance(val, dict):
            raise FeildInVaild(_('Field Invaild[{}]').format(key))

    @staticmethod
    def field_json(options, key, val):
        try:
            if isinstance(val, six.string_types):
                FeildCheck.field_string(options, key, val)
                reuslt = json.loads(val)
            else:
                reuslt = val
        except Exception:
            raise FeildInVaild(
                _('Field Invaild, type error[json][{}]').format(key))

        if not isinstance(reuslt, (dict, list)):
            raise FeildInVaild(_('Field Invaild, type error[{}]').format(key))

    @staticmethod
    def field_string(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not is_string(val):
            raise FeildInVaild(
                _('Field Invaild, type error[string][{}]').format(key))

        minlen = options.get('minlen', None)
        maxlen = options.get('maxlen', None)

        if minlen is not None and len(val) < int(minlen):
            raise FeildInVaild(
                _('Field Invaild, input length error[{}][min={}]').format(
                    key, minlen))

        if maxlen is not None and len(val) > int(maxlen):
            raise FeildInVaild(
                _('Field Invaild, input length error[{}][max={}]').format(
                    key, maxlen))

        regix = options.get('regix', None)
        if regix and re.match(regix, val) is None:
            raise FeildInVaild(
                _('Field Invaild, format error[{}][regix:{}]').format(
                    key, regix))

    @staticmethod
    def field_bytes(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        minlen = options.get('minlen', None)
        maxlen = options.get('maxlen', None)

        if minlen is not None and len(val) < int(minlen):
            raise FeildInVaild(
                _('Field Invaild, input length error[{}][min={}]').format(
                    key, minlen))

        if maxlen is not None and len(val) > int(maxlen):
            raise FeildInVaild(
                _('Field Invaild, input length error[{}][max={}]').format(
                    key, maxlen))

    @staticmethod
    def field_boolean(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not is_boolean(val):
            raise FeildInVaild(_('Field Invaild, type error[bool][{}]').format(
                key))

    @staticmethod
    def field_datetime(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not is_datetime(val):
            raise FeildInVaild(
                _('Field Invaild, type error[datetime][{}][YYYYmmDDTHHMMSS]').format(key))  # noqa

    @staticmethod
    def field_date(options, key, val):
        assert isinstance(options, dict)
        assert is_string(key)

        if not is_date(val):
            raise FeildInVaild(
                _('Field Invaild, type error[date][{}][YYYYmmDD]').format(key))  # noqa

    @staticmethod
    def field_enum(enum_name, options, key, val):
        raise NotImplementedError

    @classmethod
    def fields_insert_check(cls, field_dict, ignore_keys=None):
        assert isinstance(field_dict, dict)
        assert ignore_keys is None or isinstance(ignore_keys, (list, set))

        if ignore_keys is None:
            ignore_keys = set()
        elif isinstance(ignore_keys, list):
            ignore_keys = set(ignore_keys)
        elif isinstance(ignore_keys, set):
            pass
        else:
            raise FeildInVaild(
                _('ignore_keys invaild[{}][{}]').format(cls.__name__)
            )

        field_keys = set(field_dict.keys())
        keys_diff = cls.field_keys - field_keys
        keys_diff = keys_diff - ignore_keys
        if keys_diff:
            if IS_DEBUG:
                raise FeildInVaild(
                    _('Fields invaild, missing keys[{}][{}]').format(
                        cls.__name__, keys_diff))
            else:
                raise FeildInVaild(
                    _('Fields invaild, missing keys'))

        return cls.fields_check(field_dict)

    @classmethod
    def fields_update_check(cls, field_dict):
        cls.fields_primary_check(field_dict)

        field_keys = set(field_dict.keys())
        keys_diff = field_keys - cls.field_primary_keys
        keys_diff = keys_diff - cls.field_update_keys
        if keys_diff:
            if IS_DEBUG:
                raise FeildInVaild(
                    _('Fields are not allowed to be modified[{}][{}]').format(
                        cls.__name__, keys_diff))
            else:
                raise FeildInVaild(
                    _('Fields are not allowed to be modified'))

        return cls.fields_check(field_dict)

    @classmethod
    def fields_check(cls, field_dict):
        """fields_check."""
        assert isinstance(field_dict, dict)

        field_keys = set(field_dict.keys())
        field_keys_diff = field_keys - cls.field_keys
        if field_keys_diff:
            raise FeildInVaild(
                _('Fields Invaild, type error[{}]').format(
                    field_keys_diff))

        for key in field_keys:
            cls.field_checkx(
                key, field_dict[key],
                cls.fields[key]['type'],
                cls.fields[key]['options']
            )

    @classmethod
    def field_checkx(cls, key, val, ftype, option, check_array=True):
        args = (option, key, val)

        if check_array and option.get('is_array', False):
            if not isinstance(val, (list, set)):
                raise FeildInVaild(
                    _('Field Invaild, type error[array][{}]').format(key)
                )

            for _val in val:
                cls.field_checkx(key, _val, ftype, option, False)

        elif ftype in JSON_LIST:
            FeildCheck.field_json(*args)

        elif ftype in STRING_LIST:
            FeildCheck.field_string(*args)

        elif ftype in BYTE_LIST:
            FeildCheck.field_bytes(*args)

        elif ftype in INT_LIST:
            FeildCheck.field_int(*args)

        elif ftype in FLOAT_LIST:
            FeildCheck.field_float(*args)

        elif ftype == 'datetime':
            FeildCheck.field_datetime(*args)

        elif ftype == 'date':
            FeildCheck.field_date(*args)

        elif ftype == 'boolean':
            FeildCheck.field_boolean(*args)

        elif ftype == 'class':
            FeildCheck.field_class(*args)

        elif len(ftype) > 4 and (
                ftype[:4] == 'Enum' or
                ftype[-4:] == 'Enum'):
            cls.field_enum(
                ftype, option, key, val
            )
        else:
            raise FeildInVaild(_('Field type error[{}]').format(key))

    @classmethod
    def is_fields_vaild(cls, field_dict):
        try:
            cls.fields_check(field_dict)
        except FeildInVaild:
            return False
        else:
            return True

    @classmethod
    def fields_primary_check(cls, field_dict):
        assert isinstance(field_dict, dict)

        field_keys = set(field_dict.keys())
        field_keys_inter = field_keys & cls.field_primary_keys
        if field_keys_inter != cls.field_primary_keys:
            raise FeildInVaild(_('Fields Invaild, missing primary keys'))

    @classmethod
    def is_has_fields_primary(cls, field_dict):
        """is_has_fields_primary."""
        try:
            cls.fields_primary_check(field_dict)
        except FeildInVaild:
            return False
        else:
            return True

    @classmethod
    def filter_update(cls, field_dict):
        """filter_update."""
        assert isinstance(field_dict, dict)
        return {key: val for key, val in field_dict.items()
                if key in cls.field_primary_keys or
                key in cls.field_update_keys}

    @classmethod
    def filter_primary(cls, field_dict):
        """filter_primary."""
        assert isinstance(field_dict, dict)
        return {key: val for key, val in field_dict.items()
                if key in cls.field_primary_keys}

    @classmethod
    def filter_fields(cls, field_dict):
        """filter_fields."""
        assert isinstance(field_dict, dict)
        return {key: val for key, val in field_dict.items()
                if key in cls.field_keys}

    @classmethod
    def conv_fieldkeys(cls, field_dict):
        """conv_fieldkeys."""
        assert isinstance(field_dict, dict)
        return {cls.field_lowers[key]: [i for i in val]
                if isinstance(val, list) else val
                for key, val in field_dict.items()
                if key in cls.field_lowers}


field_check = FeildCheck.field_check
field_checks = FeildCheck.field_checks
QUERY_RESULTS = FeildOption(
    'list', _('Query Results, To See Query Json Description'),
    '[]'
)
