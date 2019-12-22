# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:02:55.

@author: name

@desc: http_sessions
"""
import sys
import six
import json
import hashlib
from tornado import gen
from tornado.web import HTTPError
from restkit.tools.error_info import error_info
from restkit.tools.biztoken import TokenField
from restkit.tools.biztoken import TokenMaker
from restkit.tools.biztoken import TokenBase as _TokenBase
from restkit.tools.configbase import WebMuserServiceSTokenSettings
from restkit.handlers.http_user_conns.http_sessions import HttpSessionBaseHandler  # noqa


class TokenBase(_TokenBase):

    sub = TokenField(str)
    iss = TokenField(str)
    aud = TokenField(str)
    jti = TokenField(str)

    nbf = TokenField(float)
    exp = TokenField(float)
    iat = TokenField(float)

    uid = TokenField(int)
    ss = TokenField(str)

    userid = 0
    sid_sign = ''

    TO_NAME_DICT = {
        'uid': 'userid',
        'ss': 'sid_sign',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    @staticmethod
    def md5(val):
        if isinstance(val, six.string_types):
            val = six.b(val)

        return hashlib.md5(val).hexdigest()[:8]

    def is_stoken_vaild(self, sid, leeway=0):
        if not self.is_vaild(leeway):
            return False

        ssign = self.md5(sid)
        if ssign != self.sid_sign:
            return False

        return True

    def is_stoken_invaild(self, sid, leeway=0):
        return not self.is_stoken_vaild(sid, leeway)


class HttpSTokenBaseHandler(HttpSessionBaseHandler):

    _session = None

    # def __init__(self, *args, **kwargs):
    #     """__init__."""
    #     super(HttpRequestHandler, self).__init__(*args, **kwargs)

    def initialize(self, **kwargs):  # noqa
        """initialize."""
        super(HttpSTokenBaseHandler, self).initialize(**kwargs)
        self.stoken_maker = TokenMaker(
            **self.gsettings.stoken_settings(self.stoken_class)
        )

    @gen.coroutine
    def rest_initialize(self, api_key, rest_option, *args, **kwargs):
        yield super(HttpSTokenBaseHandler, self).rest_initialize(
            api_key, rest_option, *args, **kwargs
        )
        self._stoken = None
        self.need_stoken = rest_option.kwargs.get('need_stoken', True)
        if self.is_stoken_invaild():
            # self.set_status(401)
            self.write_error_json(error_info.ERROR_NOT_LOGGED,
                                  append_text='[4]')
            self.finish()
            raise HTTPError(401)

    @property
    def stoken_class(self):
        return TokenBase

    @property
    def gsettings(self) -> WebMuserServiceSTokenSettings:
        return self.settings['gsettings']

    # ----------------------------------------------
    #        session
    # ----------------------------------------------

    def stoken(self, stoken_jwt=None) -> TokenBase:
        if stoken_jwt or self._stoken is None:
            self._stoken = self.stoken_maker.create_token(
                stoken_jwt
            )
        return self._stoken

    def save_stoken(self):
        stoken = self.stoken()

        self.stoken().set_option(
            'sid_sign',
            stoken.md5(self.session().session_id)
        )
        _jwt = self.stoken().sign_token()

        # if not run in pyinstaller, set to cookie, help to debug
        lscookie = self.get_query_argument('lscookie', False)
        if lscookie:
            self.set_secure_cookie('stoken', _jwt)
        return _jwt

    def is_stoken_invaild(self):
        if not self.need_stoken or not self.need_logged:
            return False

        # session must vaild
        if not self.session().is_vaild():
            return True

        sid = self.session().session_id

        # try query_argument
        stoken = self.get_query_argument('stoken', None)
        if stoken is not None and \
                self.stoken(stoken).is_stoken_vaild(sid):
            return False

        # try body_argument
        stoken = self.get_body_argument('stoken', None)
        if stoken is not None and \
                self.stoken(stoken).is_stoken_vaild(sid):
            return False

        try:
            # try body json raw
            req_data = self.decode_json_from_body()
        except json.JSONDecodeError:
            req_data = {}
        except UnicodeDecodeError:
            req_data = {}

        # try body json raw
        if isinstance(req_data, dict):
            stoken = req_data.get('stoken', None)
            if stoken is not None and \
                    self.stoken(stoken).is_stoken_vaild(sid):
                return False

        # try headers raw
        stoken = self.request.headers.get('stoken', None)
        if isinstance(stoken, bytes):
            stoken = stoken.decode()

        if stoken is not None and \
                self.stoken(stoken).is_stoken_vaild(sid):
            return False

        # try cookie raw
        stoken = self.get_secure_cookie('stoken', None)
        if isinstance(stoken, bytes):
            stoken = stoken.decode()

        if stoken is not None and \
                self.stoken(stoken).is_stoken_vaild(sid):
            return False

        return True
