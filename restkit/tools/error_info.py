# -*- coding: utf-8 -*-
"""
@create: 2019-08-23 16:11:53.

@author: name

@desc: error_info
"""
import os
import copy
import gettext
import functools
from collections import defaultdict


def gen_trans(project_name):
    trans = defaultdict(list)
    for key in DEFINE_LANGS:
        trans[key].append(gettext.translation(
            project_name,
            localedir=LANGS_PATH,
            languages=[key]
        ))
    return trans


DEFAULT_LANG = 'en'
NULL_TRANS = gettext.NullTranslations()
LANGS_LIST = os.environ.get('LANGS_LIST', 'en,en_US,zh,zh_CN')
LANGS_PATH = os.environ.get('LANGS_PATH', './config/locales')
DEFAULT_LANG = os.environ.get('LANG_DEFAULT', DEFAULT_LANG)
DEFINE_LANGS = set(LANGS_LIST.split(',') + [DEFAULT_LANG])
DEFINE_TRANS = gen_trans('restkit')


def register_trans(trans):

    if not isinstance(trans, dict):
        raise TypeError('register_trans trans invaild')

    for _trans in trans.values():
        if not isinstance(_trans, list):
            raise TypeError('register_trans trans invaild')

        for tran in _trans:
            if not isinstance(tran, gettext.NullTranslations):
                raise TypeError('register_trans trans invaild')

    if DEFAULT_LANG not in trans:
        raise TypeError('register_trans default lang tran not found')

    global DEFINE_TRANS
    for lang, _list in DEFINE_TRANS.items():
        DEFINE_TRANS[lang] = _list + trans.get(lang, [])


def register_trans_by_name(project_name):
    trans = gen_trans(project_name)
    register_trans(trans)


class TextString(object):
    """TextString."""

    FUNC_TYPE = [None, '@@add', '@@radd', '@@join',
                 '@@format', '@@format_map']

    def __init__(self, message, func=None, *args, **kwargs):
        # super(TextString, self).__init__(message)
        self.__strcache = {}
        self.__message = message
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

        if self.__func not in self.FUNC_TYPE:
            raise TypeError('func invaild')

    # ----------------------------------------------
    #        read only
    # ----------------------------------------------

    @property
    def message(self):
        return self.__message

    @property
    def func(self):
        return self.__func

    @property
    def args(self):
        return self.__args

    @property
    def kwargs(self):
        return self.__kwargs

    # ----------------------------------------------
    #        string func
    # ----------------------------------------------

    def __add__(self, other):
        return TextString(self, '@@add', other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __radd__(self, other):
        return TextString(self, '@@radd', other)

    def __mod__(self, other):
        if isinstance(other, dict):
            args = []
            kwargs = other
        else:
            args = other
            kwargs = {}

        return TextString(self, *args, **kwargs)

    def __contains__(self, key):
        return key in self.to_string()

    def find(self, sub, start=None, end=None):
        return self.to_string().find(sub, start, end)

    def format(self, *args, **kwargs):
        return TextString(self, '@@format', *args, **kwargs)

    def format_map(self, **mapping):
        return TextString(self, '@@format_map', **mapping)

    def join(self, _iter):
        return TextString(self, '@@join', _iter)

    # ----------------------------------------------
    #        languages change
    # ----------------------------------------------

    def __str__(self):
        return self.to_string()

    @staticmethod
    def t_string(lang, obj):
        return obj.to_string(lang) if isinstance(obj, TextString) else obj

    def gettext(self, message, lang=None):
        if lang is None:
            lang = DEFAULT_LANG

        trans = DEFINE_TRANS.get(lang, [])
        if not trans:
            return message

        for tran in trans:
            _message = tran.gettext(message)
            if _message != message:
                return _message

        return message

    def to_string(self, lang=None):
        if lang in self.__strcache:
            return self.__strcache[lang]

        if isinstance(self.message, TextString):
            message = self.message.to_string(lang)
        else:
            message = self.message

        t_string = functools.partial(self.t_string, lang)
        message = self.gettext(message, lang)

        # conv parames
        args = [t_string(i) for i in self.args]
        kwargs = {
            t_string(key): t_string(val)
            for key, val in self.kwargs.items()
        }

        if self.func == '@@add':
            _message = ''.join([message, args[0]])
        elif self.func == '@@radd':
            _message = ''.join([args[0], message])
        elif self.func == '@@join':
            _message = message.join(
                map(t_string, args[0])
            )
        elif self.func == '@@format':
            _message = message.format(*args, **kwargs)
        elif self.func == '@@format_map':
            _message = message.format_map(**kwargs)
        else:
            _message = message

        self.__strcache[lang] = _message
        return _message


_ = TextString
_T = TextString
_N = TextString
_L = TextString


class ErrorInfo(object):

    # Array Begin
    ERROR_SUCESS = '0'  # Sucess  # noqa
    ERROR_UNKNOW = '1'  # Unknow error  # noqa
    ERROR_DISABE_REQUEST = '2'  # Disabe request  # noqa
    ERROR_REQUEST_TIME = '3'  # Request timeout  # noqa
    ERROR_EXCEPTION = '4'  # Exception[{desc}]  # noqa
    ERROR_NOT_LOGGED = '5'  # Account Unlogged  # noqa
    ERROR_DN_EXCEPT = '6'  # Database operation failed  # noqa
    ERROR_UNKNOW_PAGE = '7'  # Unknow page  # noqa
    ERROR_DB_ERROR = '8'  # Operation failed or data not change [{table}]  # noqa
    ERROR_FIELD_CHECK_ERROR = '9'  # Missing required fields  # noqa
    ERROR_USER_IS_STOP = '10'  # This account has been disabled  # noqa
    ERROR_USER_IS_FREEZE = '11'  # This account has been freezed  # noqa
    ERROR_USER_PASSWORD_ERROR = '12'  # Password incorrect  # noqa
    ERROR_USER_INFO_NOT_FOUND = '13'  # User Not Found  # noqa
    ERROR_IP_IS_STOP = '14'  # Ip has been disabled  # noqa
    ERROR_IP_IS_FREEZE = '15'  # Ip has been freezed  # noqa
    ERROR_IP_IS_LIMIT = '16'  # Ip has been limit  # noqa
    ERROR_INPUT_INFAILD = '17'  # Input invaild[{desc}]  # noqa
    ERROR_PRODUCT_INFAILD = '18'  # Product invaild  # noqa
    ERROR_API_DISABLE = '19'  # This Api has been disabled  # noqa
    ERROR_INPUT_INFO_INFAILD = '20'  # Input invaild. data duplicate [{desc}]  # noqa
    ERROR_INPUT_INFAILD_LOGINCODE = '21'  # Input logincode invaild  # noqa
    ERROR_INPUT_INFAILD_PWD = '22'  # Input password invaild  # noqa
    ERROR_INPUT_INFAILD_IDCARD = '23'  # Input idcard invaild  # noqa
    ERROR_INPUT_INFAILD_EAMIL = '24'  # Input email invaild  # noqa
    ERROR_INPUT_INFAILD_JSONCACHE = '25'  # Input info invaild  # noqa
    ERROR_OP_OBJECT_NOT_FOUND = '26'  # Object not found[{table}]  # noqa
    ERROR_USER_NOT_FOUND = '27'  # User not found  # noqa
    ERROR_REVIEW_INFO_NOT_FOUND = '28'  # Review application not found  # noqa
    ERROR_REVIEW_IS_NOT_WAITING = '29'  # Review application has been reviewed  # noqa
    ERROR_TRADE_ERROR = '30'  # trade error[{text}]  # noqa
    ERROR_REQ_FILE_SEVEICE_ERROR = '31'  # file system error[{text}]  # noqa
    ERROR_REPORT_TASE_MAX_LIMIT = '32'  # eport export task too many. Please delete task  # noqa
    ERROR_AUTH_ERROR = '33'  # Auth error  # noqa
    ERROR_AUTH_TOKEN_TIMEOUT = '34'  # Auth Token error  # noqa
    ERROR_REQ_SIGN_ERROR = '35'  # Request sign error  # noqa
    ERROR_SAFE_LIMIT_ERROR = '36'  # Safe limit. Please sign in  # noqa
    ERROR_PRODUCT_AUTH = '37'  # Product api limit  # noqa
    ERROR_PRODUCT_USER_NOT_FOUND = '38'  # Product User not found  # noqa
    ERROR_NOT_AUTH_LIMIT = '39'  # Insufficient user rights to operate  # noqa
    ERROR_VCODE_EXPIRE_INVAILD = '40'  # Verification Code expired  # noqa
    ERROR_VCODE_LIMIT_INVAILD = '41'  # Verification Limit  # noqa
    ERROR_VCODE_ERROR_INVAILD = '42'  # Verification Code invaild  # noqa
    ERROR_SENT_LIMIT = '43'  # Send interval too short  # noqa
    ERROR_SENT_TOO_MANY_LIMIT = '44'  # Sent code Too many times, Please watting {sec}  # noqa
    ERROR_SENT_TO_TOO_MANY_LIMIT = '45'  # {to} Sent code Too many times, Please watting {sec}  # noqa
    ERROR_INFO_IS_BINDED = '46'  # {info} info is binded  # noqa
    ERROR_INFO_IS_NOT_BINDED = '47'  # {info} info is not binded  # noqa
    ERROR_INFO_NOT_MATCH = '48'  # {info} not Match  # noqa
    ERROR_EMAIL_PHONE_ALL_UNBIND = '49'  # Can not unbind, Because Email or Phone must keep one  # noqa
    ERROR_OTPINFO_NOT_FOUNT = '50'  # Email or Phone not Found  # noqa
    ERROR_FORGET_PWD_OP_LIMIT = '51'  # Forget Password operate limit  # noqa
    ERROR_PASSWORD_DEC_ERROR = '52'  # Password decode Error  # noqa
    ERROR_PUBKEY_INVAILD = '53'  # Pubkey Invaild  # noqa
    ERROR_BZTOKEN_INVAILD = '54'  # Token Invaild  # noqa
    ERROR_BZTOKEN_EXPIRED = '55'  # Token Expired  # noqa
    ERROR_GCODE_INVAILD = '56'  # Gcode Invaild  # noqa
    ERROR_API_KEY_INVAILD = '57'  # Apikey Invaild  # noqa
    ERROR_KEY_INVAILD = '58'  # {key} Invaild  # noqa
    ERROR_USER_IS_CREATED = '59'  # User has been created  # noqa
    # Array End

    ERROR_DESCRIBE = {
        # Array Begin
        ERROR_SUCESS: _(u'Sucess'),  # noqa
        ERROR_UNKNOW: _(u'Unknow error'),  # noqa
        ERROR_DISABE_REQUEST: _(u'Disabe request'),  # noqa
        ERROR_REQUEST_TIME: _(u'Request timeout'),  # noqa
        ERROR_EXCEPTION: _(u'Exception[{desc}]'),  # noqa
        ERROR_NOT_LOGGED: _(u'Account Unlogged'),  # noqa
        ERROR_DN_EXCEPT: _(u'Database operation failed'),  # noqa
        ERROR_UNKNOW_PAGE: _(u'Unknow page'),  # noqa
        ERROR_DB_ERROR: _(u'Operation failed or data not change [{table}]'),  # noqa
        ERROR_FIELD_CHECK_ERROR: _(u'Missing required fields'),  # noqa
        ERROR_USER_IS_STOP: _(u'This account has been disabled'),  # noqa
        ERROR_USER_IS_FREEZE: _(u'This account has been freezed'),  # noqa
        ERROR_USER_PASSWORD_ERROR: _(u'Password incorrect'),  # noqa
        ERROR_USER_INFO_NOT_FOUND: _(u'User Not Found'),  # noqa
        ERROR_IP_IS_STOP: _(u'Ip has been disabled'),  # noqa
        ERROR_IP_IS_FREEZE: _(u'Ip has been freezed'),  # noqa
        ERROR_IP_IS_LIMIT: _(u'Ip has been limit'),  # noqa
        ERROR_INPUT_INFAILD: _(u'Input invaild[{desc}]'),  # noqa
        ERROR_PRODUCT_INFAILD: _(u'Product invaild'),  # noqa
        ERROR_API_DISABLE: _(u'This Api has been disabled'),  # noqa
        ERROR_INPUT_INFO_INFAILD: _(u'Input invaild. data duplicate [{desc}]'),  # noqa
        ERROR_INPUT_INFAILD_LOGINCODE: _(u'Input logincode invaild'),  # noqa
        ERROR_INPUT_INFAILD_PWD: _(u'Input password invaild'),  # noqa
        ERROR_INPUT_INFAILD_IDCARD: _(u'Input idcard invaild'),  # noqa
        ERROR_INPUT_INFAILD_EAMIL: _(u'Input email invaild'),  # noqa
        ERROR_INPUT_INFAILD_JSONCACHE: _(u'Input info invaild'),  # noqa
        ERROR_OP_OBJECT_NOT_FOUND: _(u'Object not found[{table}]'),  # noqa
        ERROR_USER_NOT_FOUND: _(u'User not found'),  # noqa
        ERROR_REVIEW_INFO_NOT_FOUND: _(u'Review application not found'),  # noqa
        ERROR_REVIEW_IS_NOT_WAITING: _(u'Review application has been reviewed'),  # noqa
        ERROR_TRADE_ERROR: _(u'trade error[{text}]'),  # noqa
        ERROR_REQ_FILE_SEVEICE_ERROR: _(u'file system error[{text}]'),  # noqa
        ERROR_REPORT_TASE_MAX_LIMIT: _(u'eport export task too many. Please delete task'),  # noqa
        ERROR_AUTH_ERROR: _(u'Auth error'),  # noqa
        ERROR_AUTH_TOKEN_TIMEOUT: _(u'Auth Token error'),  # noqa
        ERROR_REQ_SIGN_ERROR: _(u'Request sign error'),  # noqa
        ERROR_SAFE_LIMIT_ERROR: _(u'Safe limit. Please sign in'),  # noqa
        ERROR_PRODUCT_AUTH: _(u'Product api limit'),  # noqa
        ERROR_PRODUCT_USER_NOT_FOUND: _(u'Product User not found'),  # noqa
        ERROR_NOT_AUTH_LIMIT: _(u'Insufficient user rights to operate'),  # noqa
        ERROR_VCODE_EXPIRE_INVAILD: _(u'Verification Code expired'),  # noqa
        ERROR_VCODE_LIMIT_INVAILD: _(u'Verification Limit'),  # noqa
        ERROR_VCODE_ERROR_INVAILD: _(u'Verification Code invaild'),  # noqa
        ERROR_SENT_LIMIT: _(u'Send interval too short'),  # noqa
        ERROR_SENT_TOO_MANY_LIMIT: _(u'Sent code Too many times, Please watting {sec}'),  # noqa
        ERROR_SENT_TO_TOO_MANY_LIMIT: _(u'{to} Sent code Too many times, Please watting {sec}'),  # noqa
        ERROR_INFO_IS_BINDED: _(u'{info} info is binded'),  # noqa
        ERROR_INFO_IS_NOT_BINDED: _(u'{info} info is not binded'),  # noqa
        ERROR_INFO_NOT_MATCH: _(u'{info} not Match'),  # noqa
        ERROR_EMAIL_PHONE_ALL_UNBIND: _(u'Can not unbind, Because Email or Phone must keep one'),  # noqa
        ERROR_OTPINFO_NOT_FOUNT: _(u'Email or Phone not Found'),  # noqa
        ERROR_FORGET_PWD_OP_LIMIT: _(u'Forget Password operate limit'),  # noqa
        ERROR_PASSWORD_DEC_ERROR: _(u'Password decode Error'),  # noqa
        ERROR_PUBKEY_INVAILD: _(u'Pubkey Invaild'),  # noqa
        ERROR_BZTOKEN_INVAILD: _(u'Token Invaild'),  # noqa
        ERROR_BZTOKEN_EXPIRED: _(u'Token Expired'),  # noqa
        ERROR_GCODE_INVAILD: _(u'Gcode Invaild'),  # noqa
        ERROR_API_KEY_INVAILD: _(u'Apikey Invaild'),  # noqa
        ERROR_KEY_INVAILD: _(u'{key} Invaild'),  # noqa
        ERROR_USER_IS_CREATED: _(u'User has been created'),  # noqa
        # Array End
    }

    @staticmethod
    def default_lang():
        return DEFAULT_LANG

    @staticmethod
    def get_langs(*args):
        for i in args:
            if i in DEFINE_LANGS:
                return i
        return DEFAULT_LANG

    @staticmethod
    def is_invaild_lang(val):
        return val not in DEFINE_TRANS

    @staticmethod
    def get_trans(lang):
        return DEFINE_TRANS.get(lang, NULL_TRANS)

    @classmethod
    def trans(cls, lang, val):
        trans = cls.get_trans(lang)
        for tran in trans:
            reuslt = tran.gettext(val)
            if reuslt != val:
                return val
        return val

    @staticmethod
    def t_string(lang, obj):
        return obj.to_string(lang) if isinstance(obj, TextString) else obj

    @classmethod
    def append_errors(cls, **kwargs):
        new_keys = set(kwargs.keys())
        old_keys = set(cls.ERROR_DESCRIBE.keys())
        same = old_keys & new_keys
        if same:
            raise TypeError(
                'error code duplicate [{}]'.format(diff)
            )
        cls.ERROR_DESCRIBE.update(kwargs)

    @classmethod
    def error_text(cls, error_num, **kwargs):
        """error_text."""
        result = cls.ERROR_DESCRIBE.get(error_num, None)
        if result is None:
            result = cls.ERROR_DESCRIBE.get(cls.ERROR_UNKNOW)

        if '{' in result and '}' in result:
            try:
                return result.format(**kwargs)
            except Exception:
                return result
        else:
            return result


error_info = ErrorInfo()
