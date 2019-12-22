# -*- coding: utf-8 -*-
"""
@create: 2018-05-16 19:43:15.

@author: name

@desc: biztoken
"""
import six
import jwt
import copy
import codecs
import datetime
from calendar import timegm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# iss: issuser
# sub: subuser
# aud: aud revicer
# exp: jwt date of expired
# nbf: jwt date of effective.
# iat: jwt create date
# jti: jwt id flag


class TokenMaker(object):

    default_settings = {
        'jwt_iss': None,
        'jwt_exp': 15 * 60,
        'jwt_mode': 'HS256',  # (HS256|RS512)
        'jwt_secret': None,
        'jwt_priv_path': None,
        'jwt_priv_pwd': None,
        'jwt_pub_path': None,
        'token_class': None,
    }

    def __init__(self, **settings):
        self.settings = copy.copy(self.default_settings)
        self.settings = settings
        self.settings.update(settings)
        self.token_class = self.settings['token_class']

        if self.token_class is None:
            self.token_class = TokenBase

        # if not isinstance(self.token_class, TokenObjectBase):
        #     raise AttributeError

        self.jwt_exp = self.settings['jwt_exp']
        self.jwt_iss = self.settings.get('jwt_iss', None)
        self.jwt_secret = self.settings.get('jwt_secret', None)
        self.jwt_priv_path = self.settings.get('jwt_priv_path', None)
        self.jwt_priv_pwd = self.settings.get('jwt_priv_pwd', None)
        self.jwt_pub_path = self.settings.get('jwt_pub_path', None)
        self.jwt_private_key = None
        self.jwt_public_key = None

        self.jwt_mode = self.settings['jwt_mode']
        if self.jwt_mode.startswith('HS'):
            if not self.jwt_secret or \
                    not isinstance(self.jwt_secret, six.string_types):
                raise TypeError('jwt_secret not set')

        elif self.jwt_mode.startswith('RS'):
            if not self.jwt_priv_pwd:
                self.jwt_priv_pwd = None
            else:
                self.jwt_priv_pwd = six.b(self.jwt_priv_pwd)

            if self.jwt_priv_path:
                self.jwt_private_key = self.load_priv_pem(
                    self.jwt_priv_path,
                    self.jwt_priv_pwd
                )
                self.jwt_public_key = self.jwt_private_key.public_key()

            elif self.jwt_pub_path or not self.jwt_public_key:
                self.jwt_public_key = self.load_pub_pem(
                    self.jwt_pub_path
                )

            if not self.jwt_public_key:
                raise TypeError('jwt_public not load')
        else:
            raise TypeError('jwt_mode invaild')

    def create_token(self, token_jwt=None):
        # assert isinstance(self.token_class, TokenObjectBase)
        return self.token_class(self, token_jwt)

    @staticmethod
    def load_pub_pem(pub_path):
        with codecs.open(pub_path, 'rb') as f:
            return serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )

    @staticmethod
    def load_priv_pem(priv_path, priv_pwd):
        with codecs.open(priv_path, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=priv_pwd,
                backend=default_backend()
            )


class TokenField(object):

    def __init__(self, dtype, defval=None):
        self.dtype = dtype
        self.defval = defval


class TokenIndex(object):

    def __init__(self, *keys):
        self.keys = keys
        self.keys_len = len(keys)
        # self.is_logged_one = is_logged_one


class TokenBase(object):
    '''TokenObjectBase.'''

    sub = TokenField(str)
    iss = TokenField(str)
    aud = TokenField(str)
    jti = TokenField(str)

    nbf = TokenField(float)
    exp = TokenField(float)
    iat = TokenField(float)

    TO_NAME_DICT = {
        'uid': 'userid',
        'lc': 'logincode',
        'un': 'username',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    def __init__(self, settings, token_jwt=None):
        if not isinstance(settings, TokenMaker):
            raise AttributeError

        self._settings = settings
        self._token_fields = self.token_fields()
        self._jwt_iss = self._settings.jwt_iss
        self._jwt_mode = self._settings.jwt_mode
        self._jwt_secret = self._settings.jwt_secret
        self._jwt_public_key = self._settings.jwt_public_key
        self._jwt_private_key = self._settings.jwt_private_key
        self._jwt_exp = self._settings.jwt_exp
        self._token_dict = {}

        if token_jwt is not None:
            self.load_token(token_jwt, True)

    # ----------------------------------------------
    #        field conv
    # ----------------------------------------------

    def parse_token(self):
        for name, value in self._token_fields.items():

            # short name set
            setattr(self, name, self.get_option(name, value.defval))

            # long name set
            if name in self.TO_NAME_DICT:
                lname = self.TO_NAME_DICT[name]
                setattr(self, lname, self.get_option(name, value.defval))

    def escaping_token(self):
        for name, value in self._token_fields.items():
            arrtval = getattr(self, name, value.defval)

            if isinstance(arrtval, TokenField):
                if value.defval is None:
                    continue
                else:
                    arrtval = value.defval

            self.set_option(name, arrtval)

    def set_option(self, name, value):
        if name in self.TO_SHORT_NAME_DICT:
            name = self.TO_SHORT_NAME_DICT[name]

        if name not in self._token_fields:
            raise AttributeError()

        setattr(self, name, value)
        self._token_dict[name] = value

    def get_option(self, name, defval=None):
        return self._token_dict.get(name, defval)

    # ----------------------------------------------
    #        time vaild
    # ----------------------------------------------

    def is_vaild(self, leeway=0):
        now = self.now()

        if self.iss and self.iss != self._jwt_iss:
            return False

        if self.nbf and self.nbf > (now + leeway):
            return False

        if self.exp and self.exp < (now - leeway):
            return False

        return True

    def now(self):
        return timegm(datetime.datetime.utcnow().utctimetuple())

    # ----------------------------------------------
    #        sign
    # ----------------------------------------------

    def load_token(self, token_jwt, raise_ex=False):
        try:
            if self._jwt_mode.startswith('HS'):
                self._token_dict = jwt.decode(
                    token_jwt,
                    self._jwt_secret,
                    algorithms=[self._jwt_mode],
                    options={
                        # 'verify_nbf': True,
                        # 'verify_aud': True,
                        # 'verify_iat': True,
                        # 'verify_iss': True,
                        # 'verify_exp': True,
                    }
                )

            elif self._jwt_mode.startswith('RS'):
                self._token_dict = jwt.decode(
                    token_jwt,
                    self._jwt_public_key,
                    algorithms=[self._jwt_mode],
                    options={
                        # 'verify_nbf': True,
                        # 'verify_aud': True,
                        # 'verify_iat': True,
                        # 'verify_iss': True,
                        # 'verify_exp': True,
                    }
                )
            else:
                raise TypeError('jwt_mode invaild')

        except jwt.exceptions.InvalidTokenError:
            if raise_ex:
                raise
            return False
        else:
            self.parse_token()
            return True

    def sign_token(self, jwt_exp=None):
        if jwt_exp is None:
            jwt_exp = self._jwt_exp

        self.escaping_token()

        now = datetime.datetime.utcnow()
        if jwt_exp:
            exp = now + datetime.timedelta(seconds=jwt_exp)
            self.set_option('exp', exp)
        self.set_option('iat', now)
        # self.set_option('nbf', now)

        # pub name
        if self._jwt_iss:
            self.set_option('iss', self._jwt_iss)

        # filter null key
        _token_dict = {
            key: val for key, val in self._token_dict.items()
            if val
        }

        # rsq sign
        if self._jwt_mode.startswith('HS'):
            return jwt.encode(
                _token_dict,
                self._jwt_secret,
                algorithm=self._jwt_mode
            ).decode('latin-1')

        elif self._jwt_mode.startswith('RS'):
            if not self._jwt_private_key:
                raise TypeError('jwt_private_key invaild')

            return jwt.encode(
                _token_dict,
                self._jwt_private_key,
                algorithm=self._jwt_mode
            ).decode('latin-1')
        else:
            raise TypeError('jwt_mode invaild')

    # ----------------------------------------------
    #        session index
    # ----------------------------------------------

    @classmethod
    def session_lname_fields(cls):
        return {cls.TO_NAME_DICT[name]
                if name in cls.TO_NAME_DICT else name: value
                for name, value in vars(cls).items()
                if isinstance(value, TokenField)}

    @classmethod
    def token_fields(cls):
        return {name: value for name, value in vars(cls).items()
                if isinstance(value, TokenField)}


class BizTokenBase(TokenBase):

    sub = TokenField(str)
    iss = TokenField(str)
    aud = TokenField(str)
    jti = TokenField(str)

    nbf = TokenField(float)
    exp = TokenField(float)
    iat = TokenField(float)

    uid = TokenField(int)
    ak = TokenField(str)

    userid = None

    TO_NAME_DICT = {
        'uid': 'userid',
        'ak': 'api_key',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    def is_token_vaild(self, api_key, leeway=0):
        if not self.is_vaild(leeway):
            return False

        if isinstance(self.ak, list):
            if api_key in self.ak:
                return False
        elif isinstance(self.ak, six.string_types):
            if api_key != self.ak:
                return False
        else:
            return False

        return True

    def is_token_invaild(self, api_key, leeway=0):
        return not self.is_token_vaild(api_key, leeway)
