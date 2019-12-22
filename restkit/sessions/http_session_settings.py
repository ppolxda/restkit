# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 13:01:10.

@author: name

@desc: http_session_settings
"""
import six
import copy
import codecs

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
except ImportError:
    default_backend = None
    serialization = None


default_session_settings = {
    'session_secret': None,
    'session_expire': 10 * 60,
    'session_key_fmt': 'session:{session_id}',
    'session_index_fmt': 'session_index:{index_name}:{index_value}:{session_id}',  # noqa
    'session_class': None,

    'jwt_iss': '',
    'jwt_mode': 'HS256',
    'jwt_secret': '',
    'jwt_priv_path': '',
    'jwt_priv_pwd': '',
    'jwt_pub_path': '',

    # 'driver': 'redis',
    # 'driver_config': {
    #     'connection_pool': None,
    #     'host': 'localhost',
    #     'port': 6637,
    # }
}


class SessionSettings(object):

    default_settings = default_session_settings

    def __init__(self, **settings):
        self.settings = copy.copy(self.default_settings)
        self.settings.update(settings)
        self.session_class = self.settings.get('session_class', SessionBase)

        # if self.settings['driver'] == 'redis':
        #     self.session_driver = RedisSessionDriver(**self.settings)
        # else:
        #     raise TypeError('driver type error')

        if self.settings['session_secret'] is None:
            raise AttributeError('session_secret not set')

        self.jwt_priv_path = self.settings.get('jwt_priv_path', None)
        self.jwt_priv_pwd = self.settings.get('jwt_priv_pwd', None)
        self.jwt_pub_path = self.settings.get('jwt_pub_path', None)
        self.jwt_mode = self.settings.get('jwt_mode', 'RS512')
        self.jwt_secret = self.settings.get('jwt_secret', None)
        self.jwt_iss = self.settings.get('jwt_iss', 'issuser')
        self.jwt_private_key = None
        self.jwt_public_key = None

        if self.jwt_mode == 'HS256':
            if not self.jwt_secret:
                raise TypeError('jwt_secret not set')
        elif self.jwt_mode == 'RS512':
            if not self.jwt_priv_pwd:
                self.jwt_priv_pwd = None
            else:
                self.jwt_priv_pwd = six.b(self.jwt_priv_pwd)

            if self.jwt_priv_path:
                self.jwt_private_key = self.load_priv_pem(self.jwt_priv_path,
                                                          self.jwt_priv_pwd)
            if self.jwt_pub_path:
                self.jwt_public_key = self.load_pub_pem(self.jwt_pub_path)

            if self.jwt_private_key is not None and \
                    self.jwt_public_key is None:
                self.jwt_public_key = self.jwt_private_key.public_key()
        else:
            raise TypeError('jwt_mode invaild')

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

    def get_session_secret(self):
        return self.settings['session_secret']

    def get_session_expire(self):
        return self.settings['session_expire']


class SessionField(object):

    def __init__(self, dtype, defval=None):
        self.dtype = dtype
        self.defval = defval


class SessionIndex(object):

    def __init__(self, *keys):
        self.keys = keys
        self.keys_len = len(keys)
        # self.is_logged_one = is_logged_one


class SessionBase(object):

    session_id = SessionField(str)
    isvaild = SessionField(bool)
    uid = SessionField(int)
    lc = SessionField(str)
    un = SessionField(str)

    TO_NAME_DICT = {
        'uid': 'userid',
        'lc': 'logincode',
        'un': 'username',
        'otps': 'otpstatus',
        'otpp': 'otppass',
    }
    TO_SHORT_NAME_DICT = {val: key for key, val in TO_NAME_DICT.items()}

    def __init__(self, session):
        self._session = session
        self._session_fields = self.session_fields()
        self._session_indexs = self.session_indexs()

        self.session_id = self._session.session_id
        # self.secret_key = self._session.secret_key
        self.isvaild = self.get_option('isvaild', self.isvaild.defval)
        self.parse_session()

    def parse_session(self):
        for name, value in self._session_fields.items():
            setattr(self, name, self.get_option(name, value.defval))

            if name in self.TO_NAME_DICT:
                lname = self.TO_NAME_DICT[name]
                setattr(self, lname, self.get_option(name, value.defval))

    def escaping_session(self):
        for name, value in self._session_fields.items():
            self.set_option(name, getattr(self, name, value.defval))

    @property
    def session_options(self):
        return self._session.session_options

    # def driver_client(self):
    #     return self._session.driver_client()

    def settings(self):
        return self._session.settings()

    def set_option(self, name, value):
        if name in self.TO_SHORT_NAME_DICT:
            name = self.TO_SHORT_NAME_DICT[name]

        if name not in self._session_fields:
            raise AttributeError()

        setattr(self, name, value)
        return self._session.set_option(name, value)

    def get_option(self, name, defval=None):
        return self._session.get_option(name, defval)

    def is_vaild(self):
        return self._session.is_vaild()

    def now(self):
        return self._session.now()

    def reload_sesion(self):
        result = self._session.reload_sesion()
        self.parse_session()
        return result

    def refresh_sesion(self):
        self.refresh_indexs()
        return self._session.refresh_sesion()

    def save_session(self):
        self.escaping_session()
        self._session.save_session()
        self.session_id = self._session.session_id
        self.save_indexs()

    @classmethod
    def session_lname_fields(cls):
        return {
            cls.TO_NAME_DICT[name]
            if name in cls.TO_NAME_DICT else name: value
            for name, value in vars(cls).items()
            if isinstance(value, SessionField)
        }

    @classmethod
    def session_fields(cls):
        return {
            name: value
            for name, value in vars(cls).items()
            if isinstance(value, SessionField)
        }

    # ----------------------------------------------
    #        index
    # ----------------------------------------------

    def __get_index_value(self, name):
        index = self._session_indexs[name]
        if index.keys_len == 1:
            return self.get_option(index.keys[0], None)
        else:
            return '_'.join([self.get_option(key, None) for key in index.keys])

    def __save_index(self, name):
        value = self.__get_index_value(name)
        self._session.save_index(name, value)

    def __refresh_index(self, name):
        value = self.__get_index_value(name)
        self._session.refresh_index(name, value)

    def save_indexs(self):
        for key in self._session_indexs.keys():
            self.__save_index(key)

    def refresh_indexs(self):
        for key in self._session_indexs.keys():
            self.__refresh_index(key)

    def clear_indexs(self, name):
        value = self.__get_index_value(name)
        self._session.clear_indexs(name, value)

    def iter_indexs(self, name):
        value = self.__get_index_value(name)
        for key in self._session.iter_indexs(name, value):
            yield key

    @classmethod
    def session_indexs(cls):
        return {name: value for name, value in vars(cls).items()
                if isinstance(value, SessionIndex)}
