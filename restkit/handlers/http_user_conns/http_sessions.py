# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:02:55.

@author: name

@desc: http_sessions
"""
import sys
import six
import uuid
import json
from tornado import gen
from tornado.web import HTTPError
from restkit.sessions import SessionBase
from restkit.sessions import SessionField
from restkit.sessions import SessionIndex
from restkit.sessions import HttpSessionHandler
from restkit.tools.error_info import error_info
from .http_base import HttpBaseHandler
from .http_base import IS_DEBUG


class EnumLoginType(object):
    """EnumLoginType."""

    LT_PWD = 1  # pwd login
    LT_SIMPLEWALLET = 2  # wallet login
    LT_SCATTER = 3  # scatter login

    enum_list = [
        LT_PWD,
        LT_SIMPLEWALLET,
        LT_SCATTER,
    ]

    @classmethod
    def is_invaild(cls, val):
        """is_invaild."""
        return val not in cls.enum_list


class EnumUFlagType(object):
    """EnumUFlagType."""

    LT_USERTYPE = 1  # USERTYPE
    LT_LOGINTYPE = 2  # LOGINTYPE
    LT_REVIEWSTATUS = 3  # REVIEWSTATUS
    LT_OTPSTATUS = 4  # OTPSTATUS
    LT_OTPPASS = 5  # OTPPASS

    enum_list = [
        LT_USERTYPE,
        LT_LOGINTYPE,
        LT_REVIEWSTATUS,
        LT_OTPSTATUS,
        LT_OTPPASS,
    ]

    @classmethod
    def mask(cls, flag):
        return 0x0f << (flag * 4)

    @classmethod
    def get_value(cls, flag, flag_val):
        mask = cls.mask(flag)
        return (flag_val & mask) >> (flag * 4)

    @classmethod
    def set_value(cls, flag, flag_val, val):
        _val = val & 0x0f
        return flag_val | (_val << (flag * 4))

    @classmethod
    def is_invaild(cls, val):
        """is_invaild."""
        return val not in cls.enum_list


class MrgSessionNew(SessionBase):

    # MrgSession
    uid = SessionField(int)
    lc = SessionField(str)
    un = SessionField(str)
    nn = SessionField(str)
    uf = SessionField(int, 0)  # userflag
    # ea = SessionField(str)
    # ut = SessionField(int, 2)
    # rs = SessionField(int, 2)
    # lt = SessionField(int, EnumLoginType.LT_PWD)
    # ph = SessionField(str)
    # em = SessionField(str)
    # tc = SessionField(str)

    # device or product
    p = SessionField(str)
    d = SessionField(str)

    # otp
    # secret_key = SessionField(str, '')
    # otps = SessionField(int, 0)  # otpstatus is need otp
    # otpp = SessionField(int, 0)  # otppass is opt pass
    rt = SessionField(int, 0)  # Refresh times
    pts = SessionField(list, [])

    # token time
    exp = SessionField(float)  # token exp
    iat = SessionField(float)  # token create time

    userid_index = SessionIndex('userid')

    # long name
    userid = None
    logincode = None
    username = None
    nikename = None
    userflag = None
    # eosaccount = None
    # phone = None
    # email = None
    reviewstatus = None
    products = []
    otpstatus = None
    otppass = None
    refreshtimes = None
    usertype = None
    logintype = None
    # telcode = None

    deviceid = None
    productid = None

    INDEX_USER_FLAG = {
        'ut': EnumUFlagType.LT_USERTYPE,
        'usertype': EnumUFlagType.LT_USERTYPE,
        'lt': EnumUFlagType.LT_LOGINTYPE,
        'logintype': EnumUFlagType.LT_LOGINTYPE,
        'rs': EnumUFlagType.LT_REVIEWSTATUS,
        'reviewstatus': EnumUFlagType.LT_REVIEWSTATUS,
        'otps': EnumUFlagType.LT_OTPSTATUS,
        'otpstatus': EnumUFlagType.LT_OTPSTATUS,
        'otpp': EnumUFlagType.LT_OTPPASS,
        'otppass': EnumUFlagType.LT_OTPPASS,
    }

    TO_NAME_DICT = {
        'uid': 'userid',
        'lc': 'logincode',
        'un': 'username',
        'nn': 'nikename',
        'uf': 'userflag',
        # 'ea': 'eosaccount',
        # 'ph': 'phone',
        # 'em': 'email',

        'rt': 'refreshtimes',
        # 'tc': 'telcode',
        'pts': 'products',

        'd': 'deviceid',
        'p': 'productid',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    # def set_option(self, name, value):
    #     if name in ['email', 'phone']:
    #         value = settings.des_encrypt(value)

    #     return super().set_option(name, value)

    # def get_option(self, name, defval=None):
    #     value = super().get_option(name, defval)
    #     if value and name in ['ph', 'em', 'email', 'phone']:
    #         value = settings.des_decrypt(value)
    #     return value

    def __init__(self, session, is_logged_one, safe_access_timeout, redis_cli):
        super().__init__(session)
        self.iat_json = {}
        self.is_logged_one = is_logged_one
        self.safe_access_timeout = safe_access_timeout
        self.redis_cli = redis_cli

    def get_userflag(self, flag):
        if self.userflag is None:
            self.userflag = 0
        elif isinstance(self.userflag, six.string_types):
            self.userflag = int(self.userflag, 'hex')

        return EnumUFlagType.get_value(flag, self.userflag)

    def set_userflag(self, flag, value):
        if self.userflag is None:
            self.userflag = 0
        elif isinstance(self.userflag, six.string_types):
            self.userflag = int(self.userflag, 'hex')

        self.userflag = EnumUFlagType.set_value(flag, self.userflag, value)

    def set_option(self, name, value):
        if name in self.INDEX_USER_FLAG:
            self.set_userflag(self.INDEX_USER_FLAG[name], value)
            return super().set_option('uf', self.userflag)
        else:
            return super().set_option(name, value)

    def get_option(self, name, defval=None):
        if name in self.INDEX_USER_FLAG:
            return self.get_userflag(self.INDEX_USER_FLAG[name])
        else:
            return super().get_option(name, defval)

    def __getattr__(self, name, default=None):
        if name in self.INDEX_USER_FLAG:
            return self.get_userflag(self.INDEX_USER_FLAG[name])
        else:
            return getattr(self, name, default)

    def parse_session(self):
        for name, value in self._session_fields.items():
            _value = self.get_option(name, value.defval)

            # unSerialization user flag
            if 'uf' == name and isinstance(_value, six.string_types):
                _value = int(_value, 0)

            # set sort name
            setattr(self, name, _value)

            # set long name
            if name in self.TO_NAME_DICT:
                lname = self.TO_NAME_DICT[name]
                setattr(self, lname, _value)

    def escaping_session(self):
        for name, value in self._session_fields.items():
            _value = getattr(self, name, value.defval)

            # Serialization user flag
            if 'uf' == name and isinstance(_value, six.integer_types):
                _value = hex(_value)

            self.set_option(name, _value)

    def __localuser_key(self):
        ssettings = self.settings()
        index_fmt = ssettings.settings['session_index_fmt']
        index_fmt = index_fmt[:index_fmt.find(':')]
        index_fmt += ':userid:' + str(self.uid)
        return index_fmt

    def delete_localuser_json(self):
        index_fmt = self.__localuser_key()
        self.redis_cli.delete(index_fmt)

    def load_localuser_json(self):
        index_fmt = self.__localuser_key()

        # check sid cache in redis
        self.iat_json = self.redis_cli.get(index_fmt)
        if not self.iat_json:
            self.iat_json = {}
            return

        try:
            self.iat_json = json.loads(self.iat_json)
        except json.JSONDecodeError:
            self.iat_json = {}

    def save_localuser_json(self, **kwargs):
        index_fmt = self.__localuser_key()
        userinfo = {
            'iat': str(self.iat),
            'username': self.username,
            # 'eosaccount': self.eosaccount,
            'logincode': self.logincode,
            'userid': self.userid
        }
        userinfo.update(kwargs)
        self.redis_cli.set(index_fmt, json.dumps(userinfo))

    def is_vaild(self):
        # is login one
        if not self.is_logged_one:
            return super(MrgSessionNew, self).is_vaild()

        result = super(MrgSessionNew, self).is_vaild()
        if not result:
            return result

        # read cache in redis
        self.load_localuser_json()

        # iat cache upgrade to dict
        if isinstance(self.iat_json, dict):
            # get iat in json
            iat = self.iat_json.get('iat', None)
        else:
            iat = None

        # check iat is newer
        if iat is None or self.iat > int(iat):
            self.save_localuser_json()
            return True

        # is login out
        return self.iat >= int(iat)

    def logout(self):
        # change iat to logout
        if not self.is_logged_one:
            return

        self.iat += 1
        self.save_localuser_json()

    def is_not_safe_limit(self):
        return (self.now() - self.iat) > self.safe_access_timeout

    def is_safe_limit(self):
        return (self.now() - self.iat) <= self.safe_access_timeout


class MrgSessionOld(SessionBase):

    # MrgSession
    uid = SessionField(int)
    lc = SessionField(str)
    un = SessionField(str)
    nn = SessionField(str)
    ea = SessionField(str)
    ut = SessionField(int, 2)
    rs = SessionField(int, 2)
    lt = SessionField(int, EnumLoginType.LT_PWD)
    # ph = SessionField(str)
    # em = SessionField(str)
    # nikename = SessionField(str)
    # tc = SessionField(str)

    # otp
    # secret_key = SessionField(str, '')
    otps = SessionField(int, 0)  # otpstatus is need otp
    otpp = SessionField(int, 0)  # otppass is opt pass
    rt = SessionField(int, 0)  # Refresh times
    pts = SessionField(list, [])

    # device or product
    p = SessionField(str)
    d = SessionField(str)

    # token time
    exp = SessionField(float)  # token exp
    iat = SessionField(float)  # token create time

    userid_index = SessionIndex('userid')

    # long name
    userid = None
    logincode = None
    username = None
    nikename = None
    userflag = None
    # phone = None
    # email = None
    reviewstatus = None
    products = []
    otpstatus = None
    otppass = None
    refreshtimes = None
    usertype = None
    logintype = None
    # telcode = None

    deviceid = None
    productid = None

    TO_NAME_DICT = {
        'uid': 'userid',
        'lc': 'logincode',
        'un': 'username',
        'nn': 'nikename',
        'rs': 'reviewstatus',
        'ph': 'phone',
        'em': 'email',
        'ut': 'usertype',
        'lt': 'logintype',
        'rt': 'refreshtimes',
        # 'tc': 'telcode',
        'pts': 'products',
        'otps': 'otpstatus',
        'otpp': 'otppass',

        'd': 'deviceid',
        'p': 'productid',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    def __init__(self, session, is_logged_one, safe_access_timeout, redis_cli):
        super().__init__(session)
        self.iat_json = {}
        self.is_logged_one = is_logged_one
        self.safe_access_timeout = safe_access_timeout
        self.redis_cli = redis_cli

    def __localuser_key(self):
        ssettings = self.settings()
        index_fmt = ssettings.settings['session_index_fmt']
        index_fmt = index_fmt[:index_fmt.find(':')]
        index_fmt += ':userid:' + str(self.uid)
        return index_fmt

    def delete_localuser_json(self):
        index_fmt = self.__localuser_key()
        self.redis_cli.delete(index_fmt)

    def load_localuser_json(self):
        index_fmt = self.__localuser_key()

        self.iat_json = self.redis_cli.get(index_fmt)
        if not self.iat_json:
            self.iat_json = {}
            return

        try:
            self.iat_json = json.loads(self.iat_json)
        except json.JSONDecodeError:
            self.iat_json = {}

    def save_localuser_json(self, **kwargs):
        index_fmt = self.__localuser_key()

        userinfo = {
            'iat': str(self.iat),
            'username': self.username,
            'logincode': self.logincode,
            'userid': self.userid
        }
        userinfo.update(kwargs)
        self.redis_cli.set(index_fmt, json.dumps(userinfo))

    def is_vaild(self):
        # is login one
        if not self.is_logged_one:
            return super(MrgSessionOld, self).is_vaild()

        result = super(MrgSessionOld, self).is_vaild()
        if not result:
            return result

        # read cache in redis
        self.load_localuser_json()

        # iat cache upgrade to dict
        if isinstance(self.iat_json, dict):
            # get iat in json
            iat = self.iat_json.get('iat', None)
        else:
            iat = None

        # check iat is newer
        if iat is None or self.iat > int(iat):
            self.save_localuser_json()
            return True

        # is login out
        return self.iat >= int(iat)

    def logout(self):
        if not self.is_logged_one:
            return

        self.iat += 1
        self.save_localuser_json()

    def is_not_safe_limit(self):
        return (self.now() - self.iat) > self.safe_access_timeout

    def is_safe_limit(self):
        return (self.now() - self.iat) <= self.safe_access_timeout


class HttpSessionBaseHandler(HttpSessionHandler, HttpBaseHandler):

    _session = None

    # def __init__(self, *args, **kwargs):
    #     """__init__."""
    #     super(HttpRequestHandler, self).__init__(*args, **kwargs)

    def initialize(self, **kwargs):  # noqa
        """initialize."""
        super(HttpSessionBaseHandler, self).initialize(**kwargs)

    @gen.coroutine
    def rest_initialize(self, api_key, rest_option, *args, **kwargs):
        yield super(HttpSessionBaseHandler, self).rest_initialize(
            api_key, rest_option, *args, **kwargs
        )
        self.product_code = rest_option.kwargs.get(
            'product_code', self.gsettings.default_product_code
        )
        self.product_check = rest_option.kwargs.get('product_check', True)

        result = self._is_session_vaild()
        if not result:
            # self.set_status(401)
            self.write_error_json(error_info.ERROR_NOT_LOGGED,
                                  append_text='[0]')
            self.finish()
            raise HTTPError(401)

        result = self._is_session_otp_pass()
        if not result:
            # self.set_status(401)
            self.write_error_json(error_info.ERROR_NOT_LOGGED,
                                  append_text='[1]')
            self.finish()
            raise HTTPError(401)

        result = self._is_session_product()
        if not result:
            # self.set_status(401)
            self.write_error_json(error_info.ERROR_PRODUCT_AUTH,
                                  append_text='[3]',
                                  pcode=self.product_code)
            self.finish()
            raise HTTPError(401)

    # ----------------------------------------------
    #        session
    # ----------------------------------------------

    def session(self, session_id=None) -> MrgSessionNew:
        if session_id or self._session is None:
            session = super().session(session_id)
            if self.gsettings.old_session:
                MrgSession = MrgSessionOld
            else:
                MrgSession = MrgSessionNew

            self._session = MrgSession(
                session,
                self.gsettings.is_logged_one,
                self.gsettings.safe_access_timeout,
                self.get_redis_cli('session_db')
            )
        return self._session

    def _is_session_product(self):
        if not self.need_logged or not self.product_check:
            return True

        # products check
        if self.product_code in self.session().products:
            return True

        return False

    def _is_session_otp_pass(self):
        if not self.need_logged or not self.need_otp_logged:
            return True

        # is session is_vaild
        if not self.session().is_vaild():
            return False

        # is session need otp
        if self.session().otps == 0:
            return True

        # is session otp pass
        if self.session().otpp == 1:
            return True

        return False

    def _is_session_vaild(self):
        if not self.need_logged:
            return True

        # try Bearer Toekn
        authtoken = self.request.headers.get('Authorization', None)
        if authtoken is not None and \
                authtoken.find('Bearer ') == 0 and \
                self.session(authtoken[len('Bearer '):]).is_vaild():
            self.session().refresh_sesion()
            return True

        # try query_argument
        sid = self.get_query_argument('sid', None)
        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        # try body_argument
        sid = self.get_body_argument('sid', None)
        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        try:
            # try body json raw
            req_data = self.decode_json_from_body()
        except json.JSONDecodeError:
            req_data = {}
        except UnicodeDecodeError:
            req_data = {}

        # try body json raw
        if isinstance(req_data, dict):
            sid = req_data.get('sid', None)
            if sid is not None and self.session(sid).is_vaild():
                self.session().refresh_sesion()
                return True

        # try cookie raw
        sid = self.get_secure_cookie('sid', None)
        if isinstance(sid, bytes):
            sid = sid.decode()

        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        return False

    def session_save(self, save_cookie=True):
        # clear user cache
        if self.gsettings.is_logged_one:
            self.session().clear_indexs('userid_index')

        # save session to redis
        self.session().set_option(
            'refreshtimes',
            self.session().refreshtimes + 1
        )
        self.session().save_session()
        self.session(self.session().session_id).save_localuser_json()

        # if not run in pyinstaller, set to cookie, help to debug
        lscookie = self.get_query_argument('lscookie', False)
        if lscookie or (save_cookie and IS_DEBUG):
            self.set_secure_cookie('sid', self.session().session_id)
        return True

    def session_userid_str(self):
        return ':'.join(['tusers', str(self.session().userid)])

    def is_need_signed(self):
        return self.gsettings.is_need_signed and\
            self.need_logged and\
            self.need_signed

    def decode_json_from_body(self):
        """b64decode=>json."""
        data = super(HttpSessionBaseHandler, self).decode_json_from_body()

        if self.is_need_signed():
            try:
                sign = data.pop('sign')
            except KeyError:
                self.write_error_json(error_info.ERROR_REQ_SIGN_ERROR,
                                      append_text='[0]')
                self.finish()
                raise HTTPError(401)

            if self.is_sign_invaild(data, sign, self.session().session_id):
                self.write_error_json(error_info.ERROR_REQ_SIGN_ERROR,
                                      append_text='[1]')
                self.finish()
                raise HTTPError(401)

        return data

    def write_error_json(self, code, text=None, **kwargs):
        try:
            no_sign = kwargs.pop('no_sign')
        except KeyError:
            no_sign = False

        req_data = self.package_rsp(code, text, **kwargs)
        if not no_sign and self.is_need_signed():
            req_data['sign'] = self.sign_json(
                req_data, self.session().session_id
            )

        self.write(self.json_dumps(req_data))

    # ----------------------------------------------
    #        sms sender
    # ----------------------------------------------

    def get_msgsender_by_session(self):
        lang = self.get_language()
        return self.gsettings.msgservice.sender_by_user(
            self.session().userid,
            self.session().logincode, lang,
            username=self.session().username
        )

    def get_msgsender_by_userid(self, userid, logincode, username=''):
        lang = self.get_language()
        return self.gsettings.msgservice.sender_by_user(
            userid, logincode, lang,
            username=username
        )

    def get_msgsender_none(self):
        return self.gsettings.msgservice.sender_by_userinfo(None)
