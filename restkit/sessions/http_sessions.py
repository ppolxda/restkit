# -*- coding: utf-8 -*-
"""
@create: 2019-10-14 19:20:55.

@author: name

@desc: http_sessions
"""
from __future__ import absolute_import, division, print_function
import time
import copy
# import hmac
import uuid
import hashlib
import datetime
import logging
import jwt
import six
from calendar import timegm
from .http_session_settings import SessionSettings

# iss: issuser
# sub: subuser
# aud: aud revicer
# exp: jwt date of expired
# nbf: jwt date of effective.
# iat: jwt create date
# jti: jwt id flag

LOGGER_LOG = logging.getLogger('restkit')


class Session(object):

    __default_options = {
        'session_id': '',
        'isvaild': False,
    }

    def __init__(self, session_settings, session_id=None):
        # self.request_handler = request_handler

        if not isinstance(session_settings, SessionSettings):
            raise TypeError('session_settings')

        settings = session_settings
        self.__ssettings = settings
        self.__sclass = settings.session_class
        self.__ssecret = self.__ssettings.get_session_secret()
        self.__sexpire = self.__ssettings.get_session_expire()
        # self.__sdriver = self.__ssettings.get_session_driver()
        self.__soptions = copy.copy(Session.__default_options)

        self.__jwt_iss = self.__ssettings.jwt_iss
        self.__jwt_private_key = self.__ssettings.jwt_private_key
        self.__jwt_public_key = self.__ssettings.jwt_public_key
        self.__jwt_mode = self.__ssettings.jwt_mode
        self.__jwt_secret = self.__ssettings.jwt_secret
        # self.secret_key = self.generate_id()
        # self.__soptions['secret_key'] = self.secret_key
        self.session_id = None

        if self.__ssecret is None:
            raise AttributeError('session_secret not set')

        if self.__jwt_mode.startswith('HS'):
            if not self.__jwt_secret:
                raise AttributeError('jwt_secret not set')
        elif self.__jwt_mode.startswith('RS'):
            if self.__jwt_private_key is None and \
                    self.__jwt_public_key is None:
                raise AttributeError('jwt_priv_path jwt_pub_path pem not set')
        else:
            raise TypeError('jwt_mode invaild')

        if session_id is not None:
            if isinstance(session_id, six.binary_type):
                try:
                    session_id = session_id.decode('utf8')
                except Exception:
                    pass

            if not isinstance(session_id, six.string_types):
                raise TypeError('session_id must is string')

            self.session_id = session_id

    def to_class(self):
        return self.__sclass(self)

    def generate_id(self):
        try:
            new_id = hashlib.sha256(self.__ssecret + str(uuid.uuid4()))
            return str(new_id.hexdigest())
        except TypeError:
            shadata = self.__ssecret + str(uuid.uuid4())
            new_id = hashlib.sha256(shadata.encode())
            return str(new_id.hexdigest())

    # def driver_client(self):
    #     return self.__sdriver.driver_client()

    def settings(self):
        return self.__ssettings

    def set_option(self, name, value):
        self.__soptions[name] = value

    def get_option(self, name, defval=None):
        return self.__soptions.get(name, defval)

    def is_vaild(self):
        return 'isvaild' in self.__soptions and \
               self.__soptions['isvaild']

    def now(self):
        return timegm(datetime.datetime.utcnow().utctimetuple())

    def reload_sesion(self):
        if self.session_id is None:
            raise AttributeError()

        if isinstance(self.session_id, six.string_types):
            session_id = six.b(self.session_id)
        else:
            session_id = self.session_id

        try:
            if self.__jwt_mode.startswith('HS'):
                self.__soptions = jwt.decode(
                    session_id,
                    self.__jwt_secret,
                    algorithms=[self.__jwt_mode],
                    options={
                        # 'verify_nbf': True,
                        # 'verify_aud': True,
                        'verify_iat': True,
                        'verify_iss': True,
                        'verify_exp': True,
                    })

            elif self.__jwt_mode.startswith('RS'):
                self.__soptions = jwt.decode(
                    session_id,
                    self.__jwt_public_key,
                    algorithms=[self.__jwt_mode],
                    options={
                        # 'verify_nbf': True,
                        # 'verify_aud': True,
                        'verify_iat': True,
                        'verify_iss': True,
                        'verify_exp': True,
                    })
            else:
                raise TypeError('jwt_mode invaild')
        except jwt.exceptions.InvalidTokenError as ex:
            LOGGER_LOG.debug('jwt error %s', ex)
            self.__soptions = {}
        except Exception:
            raise

        if self.__soptions:
            self.__soptions['isvaild'] = True
        else:
            self.__soptions['isvaild'] = False

        # self.__soptions['session_id'] = self.session_id
        # self.secret_key = self.__soptions.get('secret_key')
        # self.__soptions['session_id'] = session_id
        # self.__soptions['token_id'] = token_id

    def refresh_sesion(self):
        pass

    def save_session(self):
        # self.__soptions['secret_key'] = self.secret_key

        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                seconds=self.__sexpire),
            'iat': datetime.datetime.utcnow(),
            # 'nbf': datetime.datetime.now(),
        }
        if self.__jwt_iss:
            payload['iss'] = self.__jwt_iss

        self.__soptions.update(payload)

        if self.__jwt_mode.startswith('HS'):
            self.session_id = jwt.encode(
                {key: val for key, val in self.__soptions.items()
                 if key not in ['session_id', 'isvaild']},
                self.__jwt_secret,
                algorithm=self.__jwt_mode
            ).decode('latin-1')
        elif self.__jwt_mode.startswith('RS'):
            self.session_id = jwt.encode(
                {key: val for key, val in self.__soptions.items()
                 if key not in ['session_id', 'isvaild']},
                self.__jwt_private_key,
                algorithm=self.__jwt_mode
            ).decode('latin-1')
        else:
            raise TypeError('jwt_mode invaild')

    # ----------------------------------------------
    #        index
    # ----------------------------------------------

    def refresh_index(self, name, value):
        pass

    def save_index(self, name, value, **kwargs):
        pass

    def clear_indexs(self, name, value):
        pass

    def iter_indexs(self, name, value):
        pass
