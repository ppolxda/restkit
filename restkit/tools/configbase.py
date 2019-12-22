# -*- coding: utf-8 -*-
"""
@create: 2019-09-26 16:39:02.

@author: name

@desc: configbase
"""
import os
import re
import six
import json
import random
import socket
import base64
import decimal
import datetime
from pyopts import opts
from pyopts import FeildOption
from .biztoken import TokenMaker
from .biztoken import BizTokenBase
from .error_info import TextString
from .error_info import error_info

try:
    # Python 3.x
    from urllib.parse import urlencode, quote
except ImportError:
    # Python 2.x
    from urllib import urlencode, quote

try:
    import bcrypt
    import hashlib
    import secrets
except ImportError:
    bcrypt = None
    hashlib = None
    secrets = None


# try:
#     import redis
#     from .redis_scripts import RedisScripts
# except ImportError:
#     redis = None
#     RedisScripts = None

try:
    from report_task.tasks import ReportTaskManage
except ImportError:
    ReportTaskManage = None


try:
    from pybcexapis.tradeSystem.mgrstp.mgrstpr_grpc_apis import MgrstppbService
except ImportError:
    MgrstppbService = None


try:
    from pynotify.sender_apis import NotifySenderMrg
    from pynotify.broker.redis_broker import TaskBroker
    from pynotify.broker.redis_broker import RedisBroker
except ImportError:
    TaskBroker = object
    RedisBroker = None
    NotifySenderMrg = None


try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    default_backend = None
    serialization = None
    hashes = None
    rsa = None
    padding = None

try:
    import pyDes as pydes
except ImportError:
    pydes = None


class BaseSettings(object):

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def print_config():
        return opts.print_config(40)

    @classmethod
    def init_opt(cls, name):
        if opts.is_parse:
            return

        keys = filter(lambda x: re.match(r'^(.+)_OPT$', x), dir(cls))
        for i in keys:
            opts.add_define(getattr(cls, i))
        opts.parse_opts(name)


class MainSettings(BaseSettings):

    # ----------------------------------------------
    #        root
    # ----------------------------------------------

    ROOT_LOGGING = 'root.logging'
    ROOT_LOGGING_OPT = FeildOption(
        ROOT_LOGGING, 'string',
        default='./config/logging/logging_00.ini',
        desc='logging path',
        help_desc='logging path',
        opt_short_name='-l'
    )

    ROOT_CONFIG = 'root.config'
    ROOT_CONFIG_OPT = FeildOption(
        ROOT_CONFIG, 'string',
        default='file://./config/main_config.ini',
        desc='main config path',
        help_desc=('main config path'
                   '(file://./config/main.ini|etcd://localhost)'),
        opt_short_name='-c'
    )

    ROOT_DISABLE_EXISTING_LOGGERS = 'root.disable_existing_loggers'
    ROOT_DISABLE_EXISTING_LOGGERS_OPT = FeildOption(
        ROOT_DISABLE_EXISTING_LOGGERS, 'bool',
        default=False,
        desc='disable existing loggers',
        help_desc='disable existing loggers',
        opt_short_name='-ld'
    )


class LockSettings(BaseSettings):
    # ----------------------------------------------
    #        runtime
    # ----------------------------------------------

    ROOT_DISABLE_LOCK = 'root.disable_lock'
    ROOT_DISABLE_LOCK_OPT = FeildOption(
        ROOT_DISABLE_LOCK, 'bool',
        default=False,
        desc='disable lock file',
        help_desc='disable lock file'
    )

    MAIN_LOCK = 'main_config.lock'
    MAIN_LOCK_OPT = FeildOption(
        MAIN_LOCK, 'string',
        default='{project_name}',
        desc='lock name',
        help_desc='lock name',
        opt_short_name='-ll',
        allow_none=False
    )

    MAIN_LOCK_PATH = 'main_config.lock_path'
    MAIN_LOCK_PATH_OPT = FeildOption(
        MAIN_LOCK_PATH, 'string',
        default='./config/locks',
        desc='lock file path',
        help_desc='lock file path',
        allow_none=True
    )

    def __init__(self, *args, **kwargs):
        super(LockSettings, self).__init__(*args, **kwargs)
        self.encoding = opts.get_opt('root.encoding')
        self.lock = opts.get_opt(self.MAIN_LOCK)
        self.locks_path = opts.get_opt(self.MAIN_LOCK_PATH)
        self.disable_lock = opts.get_opt(self.ROOT_DISABLE_LOCK)


class DataBaseSettings(BaseSettings):
    """RedisSettings."""

    DBASE_PGSQL_URL = 'dbase_config.pgsql_url'
    DBASE_PGSQL_URL_OPT = FeildOption(
        DBASE_PGSQL_URL, 'string',
        default='postgresql://postgres:postgres@localhost:5432/test',
        desc='pgsql service config',
        help_desc='pgsql service config'
    )

    DBASE_PGSQL_SLAVES_URL = 'dbase_config.pgsql_slaves_url'
    DBASE_PGSQL_SLAVES_URL_OPT = FeildOption(
        DBASE_PGSQL_SLAVES_URL, 'string',
        default='postgresql://postgres:postgres@localhost:5432/test',
        desc='pgsql service slaves config',
        help_desc='pgsql service slaves config'
    )

    DBASE_PGSQL_POOL_SIZE = 'dbase_config.pgsql_pool_size'
    DBASE_PGSQL_POOL_SIZE_OPT = FeildOption(
        DBASE_PGSQL_POOL_SIZE, 'int',
        default=1,
        desc='pgsql_pool_size',
        help_desc='pgsql_pool_size'
    )

    DBASE_REDIS_URL = 'dbase_config.redis_url'
    DBASE_REDIS_URL_OPT = FeildOption(
        DBASE_REDIS_URL, 'string',
        default='redis://localhost:6379/1',
        desc='redis service config',
        help_desc='redis service config'
    )

    DBASE_MSG_URL = 'dbase_config.msg_url'
    DBASE_MSG_URL_OPT = FeildOption(
        DBASE_MSG_URL, 'string',
        default='redis://localhost:6379/5',
        desc='redis sms nodity service config',
        help_desc='redis sms nodity service config'
    )

    DBASE_MONGODB_URL = 'dbase_config.mongodb_url'
    DBASE_MONGODB_URL_OPT = FeildOption(
        DBASE_MONGODB_URL, 'string',
        default=('mongodb://localhost:27017/test'
                 '?maxPoolSize=10&connectTimeoutMS=5000'),
        desc='mongodb service config',
        help_desc='mongodb service config'
    )

    def __init__(self, *args, **kwargs):
        super(DataBaseSettings, self).__init__(*args, **kwargs)
        self.pgsql_url = opts.get_opt(self.DBASE_PGSQL_URL)
        self.pgsql_slaves_url = opts.get_opt(self.DBASE_PGSQL_SLAVES_URL)
        self.redis_url = opts.get_opt(self.DBASE_REDIS_URL)
        self.msg_url = opts.get_opt(self.DBASE_MSG_URL)
        self.mongodb_url = opts.get_opt(self.DBASE_MONGODB_URL)
        self.pgsql_pool_size = opts.get_opt(self.DBASE_PGSQL_POOL_SIZE)


class WebSettings(BaseSettings):
    """WebSetting."""

    PNAME_LISTEN_PORT = '{pname}.listen_port'
    PNAME_LISTEN_PORT_OPT = FeildOption(
        PNAME_LISTEN_PORT, 'int',
        default=5555,
        desc='webservice listen port',
        help_desc='webservice listen port'
    )

    PNAME_USE_SSH = '{pname}.use_ssh'
    PNAME_USE_SSH_OPT = FeildOption(
        PNAME_USE_SSH, 'bool',
        default=False,
        desc='is use ssh',
        help_desc='is use ssh'
    )

    DEFAULT_CERTFILE = os.path.join(os.path.abspath("./config/cert"), "server.crt")  # noqa
    PNAME_SSL_CERTFILE = '{pname}.certfile'
    PNAME_SSL_CERTFILE_OPT = FeildOption(
        PNAME_SSL_CERTFILE, 'string',
        default=DEFAULT_CERTFILE,
        desc='ssh certfile path',
        help_desc='ssh certfile path'
    )

    DEFAULT_KEYFILE = os.path.join(os.path.abspath("./config/cert"), "server.key")  # noqa
    PNAME_SSL_KEYFILE = '{pname}.keyfile'
    PNAME_SSL_KEYFILE_OPT = FeildOption(
        PNAME_SSL_KEYFILE, 'string',
        default=DEFAULT_KEYFILE,
        desc='ssh keyfile path',
        help_desc='ssh keyfile path'
    )

    PNAME_DOMAIN = '{pname}.domain'
    PNAME_DOPNAME_OPT = FeildOption(
        PNAME_DOMAIN, 'string',
        default='',
        desc='domain',
        help_desc='domain'
    )

    PNAME_NGINX_URI = '{pname}.nginx_uri'
    PNAME_NGINX_URI_OPT = FeildOption(
        PNAME_NGINX_URI, 'string',
        default='',
        desc='nginx_uri virtual path',
        help_desc='nginx_uri virtual path'
    )

    PNAME_IS_NEED_SIGNED = '{pname}.is_need_signed'
    PNAME_IS_NEED_SIGNED_OPT = FeildOption(
        PNAME_IS_NEED_SIGNED, 'bool',
        default=False,
        desc='is check package sign',
        help_desc='is check package sign'
    )

    PNAME_IS_LOGGED_ONE = '{pname}.is_logged_one'
    PNAME_IS_LOGGED_ONE_OPT = FeildOption(
        PNAME_IS_LOGGED_ONE, 'bool',
        default=False,
        desc='is logged one',
        help_desc='is logged one'
    )

    PNAME_DEFAULT_PRODUCT_CODE = '{pname}.default_product_code'
    PNAME_DEFAULT_PRODUCT_CODE_OPT = FeildOption(
        PNAME_DEFAULT_PRODUCT_CODE, 'string',
        default='',
        desc='default product code',
        help_desc='default product code'
    )

    def __init__(self, *args, **kwargs):
        super(WebSettings, self).__init__(*args, **kwargs)
        self.listen_port = opts.get_opt(self.PNAME_LISTEN_PORT)
        self.use_ssh = opts.get_opt(self.PNAME_USE_SSH)
        self.nginx_uri = opts.get_opt(self.PNAME_NGINX_URI)
        self.is_need_signed = opts.get_opt(self.PNAME_IS_NEED_SIGNED)
        self.is_logged_one = opts.get_opt(self.PNAME_IS_LOGGED_ONE)
        self.default_product_code = opts.get_opt(
            self.PNAME_DEFAULT_PRODUCT_CODE
        )

        if self.use_ssh:
            self.use_ssh_tag = 'https'
            self.ssl_options = {
                "certfile": opts.get_opt(self.PNAME_SSL_CERTFILE),
                "keyfile": opts.get_opt(self.PNAME_SSL_KEYFILE),
            }
        else:
            self.use_ssh_tag = 'http'
            self.ssl_options = None

    @property
    def domain(self):
        """domain."""
        domain = opts.get_opt(self.PNAME_DOMAIN)

        if domain is not None:
            return domain

        domain = self.get_selfhost()

        if domain is not None:
            return '{}:{}'.format(domain, self.listen_port)

        return 'localhost:{}'.format(self.listen_port)

    @staticmethod
    def format_url(ssh_tag, domain, nginx_uri, url, parames=None):
        """format_url."""
        if ssh_tag != 'https':
            ssh_tag = 'http'

        url = '{0}://{1}'.format(ssh_tag, domain) + nginx_uri + url
        if not parames:
            return url

        if isinstance(parames, dict):
            parames = urlencode(parames)
        elif isinstance(parames, six.string_types):
            parames = quote(parames, '')
        else:
            parames = parames

        return url + '?' + parames

    def make_url(self, url, parames=None):
        """make_url."""
        return self.format_url(self.use_ssh_tag,
                               self.domain,
                               self.nginx_uri,
                               url,
                               parames)

    def get_selfhost(self):
        """get_selfhost."""
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.error:
            return None

    @staticmethod
    def hash_pwd(pwd):
        if six is None:
            raise ImportError('six not install')

        if secrets is None:
            raise ImportError('secrets not install')

        if isinstance(pwd, six.string_types):
            pwd = six.b(pwd)

        salt = secrets.token_bytes(16)
        hash_data = hashlib.pbkdf2_hmac('sha512', pwd, salt, 834)
        hash_data = base64.b64encode(salt) + b'.' + base64.b64encode(hash_data)
        return hash_data.decode('utf8')

    @staticmethod
    def is_invaild_pwd(db_pwd, in_pwd):
        if six is None:
            raise ImportError('six not install')

        if bcrypt is None:
            raise ImportError('bcrypt not install')

        if isinstance(db_pwd, six.string_types):
            db_pwd = six.b(db_pwd)

        if isinstance(in_pwd, six.string_types):
            in_pwd = six.b(in_pwd)

        if db_pwd.find(b'$2b$12$') < 0 and db_pwd.find(b'.') >= 0:
            db_pwd2 = db_pwd.split(b'.')
            salt = base64.b64decode(db_pwd2[0])
            hash_data = base64.b64decode(db_pwd2[1])
            hash_data2 = hashlib.pbkdf2_hmac(
                'sha512', in_pwd, salt, 834)
            if hash_data2 == hash_data:
                return False

        try:
            result = bcrypt.checkpw(in_pwd, db_pwd)
        except Exception:
            return True
        else:
            return not result


class WebMuserServiceSettings(BaseSettings):

    MSERVICE_COOKIE_SECRET = 'web_muser_service.cookie_secret'
    MSERVICE_COOKIE_SECRET_OPT = FeildOption(
        MSERVICE_COOKIE_SECRET, 'string',
        default='test',
        desc='cookie_secret',
        help_desc='cookie_secret'
    )

    MSERVICE_SESSION_SECRET = 'web_muser_service.session_secret'
    MSERVICE_SESSION_SECRET_OPT = FeildOption(
        MSERVICE_SESSION_SECRET, 'string',
        default='test',
        desc='session_secret',
        help_desc='session_secret'
    )

    MSERVICE_SESSION_KEY_FMT = 'web_muser_service.session_key_fmt'
    MSERVICE_SESSION_KEY_FMT_OPT = FeildOption(
        MSERVICE_SESSION_KEY_FMT, 'string',
        default='session_manage:{session_id}',
        desc='session_key_fmt',
        help_desc='session_key_fmt'
    )

    MSERVICE_SESSION_INDEX_FMT = 'web_muser_service.session_index_fmt'
    MSERVICE_SESSION_INDEX_FMT_OPT = FeildOption(
        MSERVICE_SESSION_INDEX_FMT, 'string',
        default='session_manage_index:{index_name}:{index_value}:{session_id}',
        desc='session_secret',
        help_desc='session_secret'
    )

    MSERVICE_OLD_SESSION = 'web_muser_service.old_session'
    MSERVICE_OLD_SESSION_OPT = FeildOption(
        MSERVICE_OLD_SESSION, 'bool',
        default=False,
        desc='old_session',
        help_desc='old_session'
    )

    SESSION_JWT_MODE = 'web_muser_service.jwt_mode'
    SESSION_JWT_MODE_OPT = FeildOption(
        SESSION_JWT_MODE, 'string',
        default='HS256',
        desc='webservice session jwt_mode',
        help_desc=('webservice session jwt_mode')
    )

    SESSION_JWT_SECRET = 'web_muser_service.jwt_secret'
    SESSION_JWT_SECRET_OPT = FeildOption(
        SESSION_JWT_SECRET, 'string',
        default=None,
        desc='webservice session jwt_secret',
        help_desc=('webservice session jwt_secret'),
        allow_none=True
    )

    SESSION_JWT_ISS = 'web_muser_service.jwt_iss'
    SESSION_JWT_ISS_OPT = FeildOption(
        SESSION_JWT_ISS, 'string',
        default=None,
        desc='webservice session jwt_iss',
        help_desc=('webservice session jwt_iss'),
        allow_none=True
    )

    SESSION_JWT_PRIV_PATH = 'web_muser_service.jwt_priv_path'
    SESSION_JWT_PRIV_PATH_OPT = FeildOption(
        SESSION_JWT_PRIV_PATH, 'string',
        default=None,
        desc='webservice session jwt_priv_path',
        help_desc=('webservice session jwt_priv_path'),
        allow_none=True
    )

    SESSION_JWT_PRIV_PWD = 'web_muser_service.jwt_priv_pwd'
    SESSION_JWT_PRIV_PWD_OPT = FeildOption(
        SESSION_JWT_PRIV_PWD, 'string',
        default=None,
        desc='webservice session jwt_priv_pwd',
        help_desc=('webservice session jwt_priv_pwd'),
        allow_none=True
    )

    SESSION_JWT_PUB_PATH = 'web_muser_service.jwt_pub_path'
    SESSION_JWT_PUB_PATH_OPT = FeildOption(
        SESSION_JWT_PUB_PATH, 'string',
        default=None,
        desc='webservice session jwt_pub_path',
        help_desc=('webservice session jwt_pub_path'),
        allow_none=True
    )

    SESSION_JWT_TOKEN_EXP = 'web_muser_service.jwt_token_exp'
    SESSION_JWT_TOKEN_EXP_OPT = FeildOption(
        SESSION_JWT_TOKEN_EXP, 'int',
        default=3 * 60,
        desc='webservice session jwt_token_exp',
        help_desc=('webservice session jwt_token_exp'),
        allow_none=False
    )

    def __init__(self, *args, **kwargs):
        super(WebMuserServiceSettings, self).__init__(*args, **kwargs)
        self.cookie_secret = opts.get_opt(self.MSERVICE_COOKIE_SECRET)
        self.session_secret = opts.get_opt(self.MSERVICE_SESSION_SECRET)
        self.session_key_fmt = opts.get_opt(self.MSERVICE_SESSION_KEY_FMT)
        self.session_index_fmt = opts.get_opt(self.MSERVICE_SESSION_INDEX_FMT)
        self.old_session = opts.get_opt(self.MSERVICE_OLD_SESSION)

        # jwt Session Config (HS256|RS512)
        self.jwt_mode = opts.get_opt(self.SESSION_JWT_MODE)
        # jwt Session HS256
        self.jwt_secret = opts.get_opt(self.SESSION_JWT_SECRET)

        self.jwt_iss = opts.get_opt(self.SESSION_JWT_ISS)
        self.jwt_priv_path = opts.get_opt(self.SESSION_JWT_PRIV_PATH)
        self.jwt_priv_pwd = opts.get_opt(self.SESSION_JWT_PRIV_PWD)
        self.jwt_pub_path = opts.get_opt(self.SESSION_JWT_PUB_PATH)
        self.jwt_token_exp = opts.get_opt(self.SESSION_JWT_TOKEN_EXP)

        self.biztokens = TokenMaker(
            jwt_iss=self.jwt_iss,
            jwt_mode=self.jwt_mode,
            jwt_secret=self.jwt_secret,
            jwt_priv_path=self.jwt_priv_path,
            jwt_priv_pwd=self.jwt_priv_pwd,
            jwt_pub_path=self.jwt_pub_path,
            token_class=self.biztoken_class(),
            jwt_exp=self.jwt_token_exp
        )

    def biztoken_class(self):
        return BizTokenBase


class WebUserServiceSettings(WebMuserServiceSettings):

    MSERVICE_COOKIE_SECRET = 'web_user_service.cookie_secret'
    MSERVICE_COOKIE_SECRET_OPT = FeildOption(
        MSERVICE_COOKIE_SECRET, 'string',
        default='test',
        desc='cookie_secret',
        help_desc='cookie_secret'
    )

    MSERVICE_SESSION_SECRET = 'web_user_service.session_secret'
    MSERVICE_SESSION_SECRET_OPT = FeildOption(
        MSERVICE_SESSION_SECRET, 'string',
        default='test',
        desc='session_secret',
        help_desc='session_secret'
    )

    MSERVICE_SESSION_KEY_FMT = 'web_user_service.session_key_fmt'
    MSERVICE_SESSION_KEY_FMT_OPT = FeildOption(
        MSERVICE_SESSION_KEY_FMT, 'string',
        default='session_users:{session_id}',
        desc='session_key_fmt',
        help_desc='session_key_fmt'
    )

    MSERVICE_SESSION_INDEX_FMT = 'web_user_service.session_index_fmt'
    MSERVICE_SESSION_INDEX_FMT_OPT = FeildOption(
        MSERVICE_SESSION_INDEX_FMT, 'string',
        default='session_users_index:{index_name}:{index_value}:{session_id}',
        desc='session_secret',
        help_desc='session_secret'
    )

    MSERVICE_OLD_SESSION = 'web_user_service.old_session'
    MSERVICE_OLD_SESSION_OPT = FeildOption(
        MSERVICE_OLD_SESSION, 'bool',
        default=False,
        desc='old_session',
        help_desc='old_session'
    )

    SESSION_JWT_MODE = 'web_user_service.jwt_mode'
    SESSION_JWT_MODE_OPT = FeildOption(
        SESSION_JWT_MODE, 'string',
        default='HS256',
        desc='webservice session jwt_mode',
        help_desc=('webservice session jwt_mode')
    )

    SESSION_JWT_SECRET = 'web_user_service.jwt_secret'
    SESSION_JWT_SECRET_OPT = FeildOption(
        SESSION_JWT_SECRET, 'string',
        default=None,
        desc='webservice session jwt_secret',
        help_desc=('webservice session jwt_secret'),
        allow_none=True
    )

    SESSION_JWT_ISS = 'web_user_service.jwt_iss'
    SESSION_JWT_ISS_OPT = FeildOption(
        SESSION_JWT_ISS, 'string',
        default=None,
        desc='webservice session jwt_iss',
        help_desc=('webservice session jwt_iss'),
        allow_none=True
    )

    SESSION_JWT_PRIV_PATH = 'web_user_service.jwt_priv_path'
    SESSION_JWT_PRIV_PATH_OPT = FeildOption(
        SESSION_JWT_PRIV_PATH, 'string',
        default=None,
        desc='webservice session jwt_priv_path',
        help_desc=('webservice session jwt_priv_path'),
        allow_none=True
    )

    SESSION_JWT_PRIV_PWD = 'web_user_service.jwt_priv_pwd'
    SESSION_JWT_PRIV_PWD_OPT = FeildOption(
        SESSION_JWT_PRIV_PWD, 'string',
        default=None,
        desc='webservice session jwt_priv_pwd',
        help_desc=('webservice session jwt_priv_pwd'),
        allow_none=True
    )

    SESSION_JWT_PUB_PATH = 'web_user_service.jwt_pub_path'
    SESSION_JWT_PUB_PATH_OPT = FeildOption(
        SESSION_JWT_PUB_PATH, 'string',
        default=None,
        desc='webservice session jwt_pub_path',
        help_desc=('webservice session jwt_pub_path'),
        allow_none=True
    )

    SESSION_JWT_TOKEN_EXP = 'web_user_service.jwt_token_exp'
    SESSION_JWT_TOKEN_EXP_OPT = FeildOption(
        SESSION_JWT_TOKEN_EXP, 'int',
        default=3 * 60,
        desc='webservice session jwt_token_exp',
        help_desc=('webservice session jwt_token_exp'),
        allow_none=False
    )


class WebMuserServiceSTokenSettings(BaseSettings):

    STOKEN_JWT_MODE = 'web_muser_service.stoken_jwt_mode'
    STOKEN_JWT_MODE_OPT = FeildOption(
        STOKEN_JWT_MODE, 'string',
        default='HS256',
        desc='webservice stoken jwt_mode',
        help_desc=('webservice stoken jwt_mode')
    )

    STOKEN_JWT_SECRET = 'web_muser_service.stoken_jwt_secret'
    STOKEN_JWT_SECRET_OPT = FeildOption(
        STOKEN_JWT_SECRET, 'string',
        default=None,
        desc='webservice stoken jwt_secret',
        help_desc=('webservice stoken jwt_secret'),
        allow_none=True
    )

    STOKEN_JWT_ISS = 'web_muser_service.stoken_jwt_iss'
    STOKEN_JWT_ISS_OPT = FeildOption(
        STOKEN_JWT_ISS, 'string',
        default=None,
        desc='webservice stoken jwt_iss',
        help_desc=('webservice stoken jwt_iss'),
        allow_none=True
    )

    STOKEN_JWT_PRIV_PATH = 'web_muser_service.stoken_jwt_priv_path'
    STOKEN_JWT_PRIV_PATH_OPT = FeildOption(
        STOKEN_JWT_PRIV_PATH, 'string',
        default=None,
        desc='webservice stoken jwt_priv_path',
        help_desc=('webservice stoken jwt_priv_path'),
        allow_none=True
    )

    STOKEN_JWT_PRIV_PWD = 'web_muser_service.stoken_jwt_priv_pwd'
    STOKEN_JWT_PRIV_PWD_OPT = FeildOption(
        STOKEN_JWT_PRIV_PWD, 'string',
        default=None,
        desc='webservice stoken jwt_priv_pwd',
        help_desc=('webservice stoken jwt_priv_pwd'),
        allow_none=True
    )

    STOKEN_JWT_PUB_PATH = 'web_muser_service.stoken_jwt_pub_path'
    STOKEN_JWT_PUB_PATH_OPT = FeildOption(
        STOKEN_JWT_PUB_PATH, 'string',
        default=None,
        desc='webservice stoken jwt_pub_path',
        help_desc=('webservice stoken jwt_pub_path'),
        allow_none=True
    )

    STOKEN_JWT_TOKEN_EXP = 'web_muser_service.stoken_jwt_token_exp'
    STOKEN_JWT_TOKEN_EXP_OPT = FeildOption(
        STOKEN_JWT_TOKEN_EXP, 'int',
        default=3 * 60,
        desc='webservice stoken jwt_token_exp',
        help_desc=('webservice stoken jwt_token_exp'),
        allow_none=False
    )

    def __init__(self, *args, **kwargs):
        super(WebMuserServiceSTokenSettings, self).__init__(*args, **kwargs)
        # jwt Session Config (HS256|RS512)
        self.stoken_jwt_mode = opts.get_opt(self.STOKEN_JWT_MODE)
        # jwt Session HS256
        self.stoken_jwt_secret = opts.get_opt(self.STOKEN_JWT_SECRET)

        self.stoken_jwt_iss = opts.get_opt(self.STOKEN_JWT_ISS)
        self.stoken_jwt_priv_path = opts.get_opt(self.STOKEN_JWT_PRIV_PATH)
        self.stoken_jwt_priv_pwd = opts.get_opt(self.STOKEN_JWT_PRIV_PWD)
        self.stoken_jwt_pub_path = opts.get_opt(self.STOKEN_JWT_PUB_PATH)
        self.stoken_jwt_token_exp = opts.get_opt(self.STOKEN_JWT_TOKEN_EXP)

    def stoken_settings(self, token_class):
        return {
            'jwt_iss': self.stoken_jwt_iss,
            'jwt_exp': self.stoken_jwt_token_exp,
            'jwt_mode': self.stoken_jwt_mode,  # (HS256|RS512)
            'jwt_secret': self.stoken_jwt_secret,
            'jwt_priv_path': self.stoken_jwt_priv_path,
            'jwt_priv_pwd': self.stoken_jwt_priv_pwd,
            'jwt_pub_path': self.stoken_jwt_pub_path,
            'token_class': token_class,
        }


class WebUserServiceSTokenSettings(WebMuserServiceSTokenSettings):

    STOKEN_JWT_MODE = 'web_user_service.stoken_jwt_mode'
    STOKEN_JWT_MODE_OPT = FeildOption(
        STOKEN_JWT_MODE, 'string',
        default='HS256',
        desc='webservice stoken jwt_mode',
        help_desc=('webservice stoken jwt_mode')
    )

    STOKEN_JWT_SECRET = 'web_user_service.stoken_jwt_secret'
    STOKEN_JWT_SECRET_OPT = FeildOption(
        STOKEN_JWT_SECRET, 'string',
        default=None,
        desc='webservice stoken jwt_secret',
        help_desc=('webservice stoken jwt_secret'),
        allow_none=True
    )

    STOKEN_JWT_ISS = 'web_user_service.stoken_jwt_iss'
    STOKEN_JWT_ISS_OPT = FeildOption(
        STOKEN_JWT_ISS, 'string',
        default=None,
        desc='webservice stoken jwt_iss',
        help_desc=('webservice stoken jwt_iss'),
        allow_none=True
    )

    STOKEN_JWT_PRIV_PATH = 'web_user_service.stoken_jwt_priv_path'
    STOKEN_JWT_PRIV_PATH_OPT = FeildOption(
        STOKEN_JWT_PRIV_PATH, 'string',
        default=None,
        desc='webservice stoken jwt_priv_path',
        help_desc=('webservice stoken jwt_priv_path'),
        allow_none=True
    )

    STOKEN_JWT_PRIV_PWD = 'web_user_service.stoken_jwt_priv_pwd'
    STOKEN_JWT_PRIV_PWD_OPT = FeildOption(
        STOKEN_JWT_PRIV_PWD, 'string',
        default=None,
        desc='webservice stoken jwt_priv_pwd',
        help_desc=('webservice stoken jwt_priv_pwd'),
        allow_none=True
    )

    STOKEN_JWT_PUB_PATH = 'web_user_service.stoken_jwt_pub_path'
    STOKEN_JWT_PUB_PATH_OPT = FeildOption(
        STOKEN_JWT_PUB_PATH, 'string',
        default=None,
        desc='webservice stoken jwt_pub_path',
        help_desc=('webservice stoken jwt_pub_path'),
        allow_none=True
    )

    STOKEN_JWT_TOKEN_EXP = 'web_user_service.stoken_jwt_token_exp'
    STOKEN_JWT_TOKEN_EXP_OPT = FeildOption(
        STOKEN_JWT_TOKEN_EXP, 'int',
        default=3 * 60,
        desc='webservice stoken jwt_token_exp',
        help_desc=('webservice stoken jwt_token_exp'),
        allow_none=False
    )


class CommonSettings(BaseSettings):
    # ----------------------------------------------
    #        runtime
    # ----------------------------------------------

    COMMON_PHONE_USER_AGENT = 'common_config.phone_user_agent'
    COMMON_PHONE_USER_AGENT_OPT = FeildOption(
        COMMON_PHONE_USER_AGENT, 'string',
        default='',
        desc='phone agent regix',
        help_desc='phone agent regix'
    )

    def __init__(self, *args, **kwargs):
        super(CommonSettings, self).__init__(*args, **kwargs)
        self.phone_user_agent = opts.get_opt(
            self.COMMON_PHONE_USER_AGENT
        )
        if self.phone_user_agent:
            self.phone_user_agent = re.compile(
                self.phone_user_agent, re.IGNORECASE)
        else:
            self.phone_user_agent = None

    def is_mobile(self, val):
        if not self.phone_user_agent:
            return None

        return re.match(self.phone_user_agent, val) is not None


class LoginLimitSettings(DataBaseSettings):
    """LoginLimitSettings."""

    AUTH_LOGIN_KEY = 'auth_login_verify:{}'
    AUTH_LOGIN_CODE_KEY = 'auth_login_verify_captcha:{}'
    AUTH_LOGIN_PWD_ERROR_KEY = 'auth_login_verify_pwd_error_count:{}'
    AUTH_LOGIN_IP_ERROR_KEY = 'auth_login_verify_ip_error_count:{}'
    AUTH_LOGIN_RESEND_KEY = 'auth_login_verify_captcha:uid:{}:resend_limit'

    TO_SIGN_TIMEOUT = 'timeout_config.sign_timeout'
    TO_SIGN_TIMEOUT_OPT = FeildOption(
        TO_SIGN_TIMEOUT, 'int',
        default=5 * 60,
        desc='request sign timeout',
        help_desc='request sign timeout'
    )

    TO_LOGIN_SID_TIMEOUT = 'timeout_config.login_sid_timeout'
    TO_LOGIN_SID_TIMEOUT_OPT = FeildOption(
        TO_LOGIN_SID_TIMEOUT, 'int',
        default=10 * 60,
        desc='login session timeout',
        help_desc='login session timeout'
    )

    TO_SAFE_ACCESS_TIMEOUT = 'timeout_config.safe_access_timeout'
    TO_SAFE_ACCESS_TIMEOUT_OPT = FeildOption(
        TO_SAFE_ACCESS_TIMEOUT, 'int',
        default=900,
        desc='safe_access_timeout',
        help_desc='safe_access_timeout'
    )

    TO_APIKEY_CHECK = 'timeout_config.apikey_check'
    TO_APIKEY_CHECK_OPT = FeildOption(
        TO_APIKEY_CHECK, 'bool',
        default=True,
        desc='safe_access_timeout',
        help_desc='safe_access_timeout'
    )

    def __init__(self, *args, **kwargs):
        super(LoginLimitSettings, self).__init__(*args, **kwargs)
        self.sign_timeout = opts.get_opt(self.TO_SIGN_TIMEOUT)
        self.login_sid_timeout = opts.get_opt(self.TO_LOGIN_SID_TIMEOUT)
        self.safe_access_timeout = opts.get_opt(self.TO_SAFE_ACCESS_TIMEOUT)
        self.apikey_check = opts.get_opt(self.TO_APIKEY_CHECK)


class CsvReportSettings(BaseSettings):
    """CsvReportSettings."""

    DBASE_PGSQL_SLAVES_URL = 'dbase_config.pgsql_slaves_url'
    DBASE_PGSQL_SLAVES_URL_OPT = FeildOption(
        DBASE_PGSQL_SLAVES_URL, 'string',
        default='postgresql://postgres:postgres@localhost:5432/test',
        desc='pgsql service slaves config',
        help_desc='pgsql service slaves config'
    )

    DBASE_REPORT_URL = 'dbase_config.report_url'
    DBASE_REPORT_URL_OPT = FeildOption(
        DBASE_REPORT_URL, 'string',
        default=('mongodb://localhost:27017/test'
                 '?maxPoolSize=10&connectTimeoutMS=5000'),
        desc='redis sms nodity service config',
        help_desc='redis sms nodity service config'
    )

    CSV_REPORT_MAX_RECORD_LIMIT = 'dbase_config.max_record_limit'
    CSV_REPORT_MAX_RECORD_LIMIT_OPT = FeildOption(
        CSV_REPORT_MAX_RECORD_LIMIT, 'int',
        default=100000,
        desc='max_record_limit',
        help_desc='max_record_limit'
    )

    CSV_REPORT_MAX_TASK_LIMIT = 'dbase_config.max_task_limit'
    CSV_REPORT_MAX_TASK_LIMIT_OPT = FeildOption(
        CSV_REPORT_MAX_TASK_LIMIT, 'int',
        default=100000,
        desc='max_task_limit',
        help_desc='max_task_limit'
    )

    def __init__(self, *args, **kwargs):
        super(CsvReportSettings, self).__init__(*args, **kwargs)
        if ReportTaskManage is None:
            raise ImportError('report_task.tasks.ReportTaskManage')

        self.report_url = opts.get_opt(self.DBASE_REPORT_URL)
        self.pgsql_slaves_url = opts.get_opt(self.DBASE_PGSQL_SLAVES_URL)
        self.max_task_limit = opts.get_opt(self.CSV_REPORT_MAX_TASK_LIMIT)
        self.max_record_limit = opts.get_opt(self.CSV_REPORT_MAX_RECORD_LIMIT)
        self.max_record_limit = (self.max_record_limit, 0)
        self.csvtask = ReportTaskManage(**{
            'host': self.report_url,
            'auto_commit': False
        })

    def csv_add_task(self, userid, sql_str, sql_parames,
                     cnname, options, **kwargs):
        task_count = self.csvtask.count_tasks_by_userid(userid)

        if task_count > self.max_task_limit:
            raise TypeError('report task too many')

        if 'FOR UPDATE' in sql_str:
            raise TypeError('sql must not has FOR UPDATE')

        if 'LIMIT' in sql_str:
            sql_str = sql_str[:sql_str.rfind('LIMIT')]
            sql_str += ' LIMIT %s OFFSET %s' % self.max_record_limit
        else:
            sql_str += ' LIMIT %s OFFSET %s' % self.max_record_limit

        try:
            sops = kwargs.pop('sops')
        except KeyError:
            sops = None

        if sops is not None:
            if not isinstance(sops, list):
                raise TypeError('sops invaild')

            for l in sops:
                if not isinstance(l, dict):
                    raise TypeError('sops invaild')

                if 'key' not in l:
                    raise TypeError('sops.key invaild')

                if 'cnname' not in l:
                    raise TypeError('sops.cnname invaild')

                if 'options' not in l:
                    raise TypeError('sops.options invaild')

        kwargs['userid'] = userid
        task = self.csvtask.create_task(self.pgsql_slaves_url,
                                        sql_str, sql_parames, cnname,
                                        options, sops, **kwargs)

        task.add_task()


class PybcexapisSettings(BaseSettings):
    """PybcexapisSettings."""

    TRADE_TRADE_GRPC_HOST = 'trade_config.trade_grpc_host'
    TRADE_TRADE_GRPC_HOST_OPT = FeildOption(
        TRADE_TRADE_GRPC_HOST, 'string',
        default='localhost:5432',
        desc='trade_grpc_host',
        help_desc='trade_grpc_host'
    )

    def __init__(self, *args, **kwargs):
        super(PybcexapisSettings, self).__init__(*args, **kwargs)
        if MgrstppbService is None:
            raise ImportError(
                'pybcexapis.tradeSystem.mgrstp.'
                'mgrstp_grpc_apis.MgrstppbService'
            )

        self.trade_grpc_host = opts.get_opt(self.TRADE_TRADE_GRPC_HOST)
        self.tservice = MgrstppbService(self.trade_grpc_host)


class AuthTaskBroker(TaskBroker):

    # def to_string(self):
    #     return self.json_dumps(self.to_dict())

    def get_language(self):
        return self.parames.get('lang', error_info.default_lang())

    def json_dumps(self, jsonstring):
        return json.dumps(jsonstring, default=self.json_serial)

    def json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y%m%dT%H%M%S")

        if isinstance(obj, datetime.date):
            return obj.strftime("%Y%m%d")

        if isinstance(obj, decimal.Decimal):
            return str(obj)

        elif isinstance(obj, TextString):
            return obj.to_string(self.get_language())

        raise TypeError("Type %s not serializable" % type(obj))


class UserNotifySettings(BaseSettings):
    """UserNotifySettings."""

    DBASE_MSG_URL = 'dbase_config.msg_url'
    DBASE_MSG_URL_OPT = FeildOption(
        DBASE_MSG_URL, 'string',
        default='redis://localhost:6379/5',
        desc='redis sms notify service config',
        help_desc='redis sms notify service config'
    )

    DBASE_MSG_PRODUCT_NAME = 'dbase_config.msg_product_name'
    DBASE_MSG_PRODUCT_NAME_OPT = FeildOption(
        DBASE_MSG_PRODUCT_NAME, 'string',
        default='test service',
        desc='msg_product_name',
        help_desc='msg_product_name'
    )

    def __init__(self, *args, **kwargs):
        super(UserNotifySettings, self).__init__(*args, **kwargs)
        if NotifySenderMrg is None:
            raise ImportError(
                'pynotify.sender_apis.NotifySenderMrg'
            )

        self.msg_url = opts.get_opt(self.DBASE_MSG_URL)
        self.product_name = opts.get_opt(self.DBASE_MSG_PRODUCT_NAME)

        self.msgbroker = RedisBroker(
            self.msg_url, taskbroker=self.task_broker_class()
        )
        self.msgservice = NotifySenderMrg(self.msgbroker, self.product_name)

    def task_broker_class(self):
        return AuthTaskBroker


class RsaEncryptSettings(BaseSettings):
    """RsaEncryptSettings."""

    CERT_RSA_KEYS_PATH = 'cert_config.rsa_keys_path'
    CERT_RSA_KEYS_PATH_OPT = FeildOption(
        CERT_RSA_KEYS_PATH, 'string',
        default='./config/rsa_keys',
        desc='rsa_keys_path',
        help_desc='rsa_keys_path'
    )

    def __init__(self, *args, **kwargs):
        super(RsaEncryptSettings, self).__init__(*args, **kwargs)

        if default_backend is None:
            raise ImportError('cryptography not install')

        self.__rsa_keys_path = opts.get_opt(self.CERT_RSA_KEYS_PATH)
        self.__rsa_keys = {}
        self.__rsa_pub_keys = []

        if not os.path.exists(self.__rsa_keys_path):
            return

        pathlist = os.listdir(self.__rsa_keys_path)
        for path in pathlist:
            fullpath = os.path.join(self.__rsa_keys_path, path)
            _, suffix = os.path.splitext(path)

            if suffix != '.pem':
                continue

            with open(fullpath, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
                public_key = private_key.public_key()
                pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                pem = pem.splitlines()
                pem = pem[1:-1]
                # begin_key = '-----BEGIN PRIVATE KEY-----'
                # end_key = '-----END PRIVATE KEY-----'
                pem = six.b('').join(pem)
                self.__rsa_keys[pem] = private_key

        self.__rsa_pub_keys = [key.decode('latin-1')
                               for key in self.__rsa_keys.keys()]

        # key, data = self.rsa_encrypt('aaaaa')
        # data2 = self.rsa_decrypt(key, data)
        # print(data2)

    def rsa_pubkey(self):
        return random.choice(self.__rsa_pub_keys)

    def rsa_genkey(self, pwd):
        if isinstance(pwd, six.string_types):
            pwd = six.b(pwd)

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(pwd)
        )
        pem.splitlines()[1]
        pem = pem[1:-1]
        pem = six.b('').join(pem)
        private_key = pem

        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pem = pem.splitlines()
        pem = pem[1:-1]
        pem = six.b('').join(pem)
        public_key = pem
        return public_key, private_key

    def rsa_encrypt(self, data):
        if isinstance(data, six.string_types):
            data = six.b(data)

        pubkey = six.b(self.rsa_pubkey())
        # privkey = self.rsa_keys[pubkey]
        pub_key = self.__rsa_keys[pubkey].public_key()

        ciphertext = pub_key.encrypt(
            data,
            padding.PKCS1v15()
            # padding.OAEP(
            #     mgf=padding.MGF1(algorithm=hashes.SHA256()),
            #     algorithm=hashes.SHA256(),
            #     label=None
            # )
        )
        ciphertext = base64.b64encode(ciphertext)
        return pubkey, ciphertext

    def rsa_decrypt(self, pubkey, data):
        if isinstance(data, six.string_types):
            data = six.b(data)

        if isinstance(pubkey, six.string_types):
            pubkey = six.b(pubkey)

        data = base64.b64decode(data)
        privkey = self.__rsa_keys.get(pubkey, None)
        if not privkey:
            return None

        ciphertext = privkey.decrypt(
            data,
            padding.PKCS1v15()
        )
        return ciphertext


class DesEncryptSettings(BaseSettings):
    """DesEncryptSettings."""

    CERT_DES_KEY = 'cert_config.des_key'
    CERT_DES_KEY_OPT = FeildOption(
        CERT_DES_KEY, 'string',
        default='sjgJeeudEIyGBfOOf5hineaV',
        desc='des_key',
        help_desc='des_key'
    )

    CERT_DES_VI = 'cert_config.des_vi'
    CERT_DES_VI_OPT = FeildOption(
        CERT_DES_VI, 'string',
        default='jvngd7fa',
        desc='des_vi',
        help_desc='des_vi'
    )

    def __init__(self, *args, **kwargs):
        super(DesEncryptSettings, self).__init__(*args, **kwargs)

        if pydes is None:
            raise ImportError('pyDes not install')

        self.des_key = opts.get_opt(self.CERT_DES_KEY)
        self.des_vi = opts.get_opt(self.CERT_DES_VI)

        if self.des_key is None or self.des_vi is None:
            raise ImportError('pyaes des_key or des_vi not set')

        self.des_key = six.b(self.des_key)
        self.des_vi = six.b(self.des_vi)
        self.des = pydes.triple_des(
            self.des_key, pydes.ECB, self.des_vi,
            pad=None, padmode=pydes.PAD_PKCS5)

    def des_encrypt(self, data, key=None, vi=None):
        if isinstance(data, six.string_types):
            data = six.b(data)

        if key is not None and vi is not None:
            des = pydes.triple_des(
                key, pydes.ECB, vi, pad=None, padmode=pydes.PAD_PKCS5)
        elif key is not None and vi is None:
            des = pydes.triple_des(
                key, pydes.ECB, self.des_vi, pad=None, padmode=pydes.PAD_PKCS5)
        elif key is None and vi is not None:
            des = pydes.triple_des(
                self.des_key, pydes.ECB, vi, pad=None, padmode=pydes.PAD_PKCS5)
        else:
            des = self.des

        data = des.encrypt(data)
        return base64.b64encode(data).decode('utf8')

    def des_decrypt(self, data, key=None, vi=None):
        if isinstance(data, six.string_types):
            data = six.b(data)

        if key is not None and vi is not None:
            des = pydes.triple_des(
                key, pydes.ECB, vi, pad=None, padmode=pydes.PAD_PKCS5)
        elif key is not None and vi is None:
            des = pydes.triple_des(
                key, pydes.ECB, self.des_vi, pad=None, padmode=pydes.PAD_PKCS5)
        elif key is None and vi is not None:
            des = pydes.triple_des(
                self.des_key, pydes.ECB, vi, pad=None, padmode=pydes.PAD_PKCS5)
        else:
            des = self.des

        data = base64.b64decode(data)
        return des.decrypt(data).decode('utf8')


# class LoginSetting(DataBaseSettings):
#     """SystemLimitSetting."""

#     def __init__(self, *args, **kwargs):
#         self.login_limit_piccode_count = self.get_value_int_def(
#             'timeout_config', 'login_limit_piccode_count', 5)

#         self.login_limit_piccode_timeout = self.get_value_int_def(
#             'timeout_config', 'login_limit_piccode_timeout', 60 * 60)

#         self.login_pwd_freeze_count = self.get_value_int_def(
#             'timeout_config', 'login_pwd_freeze_count', 30 * 60)

#         self.login_pwd_freeze_timeout = self.get_value_int_def(
#             'timeout_config', 'login_pwd_freeze_timeout', 30 * 60)

#         self.login_ip_freeze_count = self.get_value_int_def(
#             'timeout_config', 'login_ip_freeze_count', 30 * 60)

#         self.login_ip_freeze_timeout = self.get_value_int_def(
#             'timeout_config', 'login_ip_freeze_timeout', 30 * 60)
        # self.resend_limit = self.get_value_int_def(
        #     'timeout_config', 'resend_limit', 180)
#     def __init_login_redis(self):
#         if self.__login_redis is None:
#             self.__login_redis = redis.from_url(**{
#                 'url': self.redis_url,
#                 'decode_responses': True
#             })
#         return self.__login_redis

#     # ----------------------------------------------
#     #        login Image captcha
#     # ----------------------------------------------

#     # @staticmethod
#     # def __random_number(size=6):
#     #     return ''.join([random.choice(string.digits) for i in range(size)])

#     # @staticmethod
#     # def _gen_login_captcha():
#     #     image = ImageCaptcha()
#     #     code = SystemLimitSetting.__random_number(6)
#     #     return code, image.generate(code)

#     def gen_login_captcha(self, logincode):
#         code, code_img = self._gen_login_captcha()
#         client = self.__init_login_redis()
#         client.set(self.AUTH_LOGIN_CODE_KEY.format(logincode),
#                    code, ex=self.login_limit_piccode_timeout)
#         return code_img

#     def get_login_captcha(self, logincode):
#         client = self.__init_login_redis()
#         result = client.get(
#             self.AUTH_LOGIN_CODE_KEY.format(logincode))
#         if result is None:
#             return None
#         return result

#     # ----------------------------------------------
#     #        password count
#     # ----------------------------------------------

#     def incr_login_pwd_error_count(self, logincode):
#         client = self.__init_login_redis()
#         pipe = client.pipeline()
#         pipe.incr(self.AUTH_LOGIN_PWD_ERROR_KEY.format(logincode))
#         pipe.expire(self.AUTH_LOGIN_PWD_ERROR_KEY.format(logincode),
#                     self.login_pwd_freeze_timeout)
#         return pipe.execute()

#     def get_login_pwd_error_count(self, logincode):
#         client = self.__init_login_redis()
#         result = client.get(self.AUTH_LOGIN_PWD_ERROR_KEY.format(logincode))
#         return 0 if result is None else int(result)

#     def is_login_pwd_error_limit(self, logincode):
#         count = self.get_login_pwd_error_count(logincode)
#         return count > self.login_pwd_freeze_count

#     def is_login_need_piccode_limit(self, logincode):
#         count = self.get_login_pwd_error_count(logincode)
#         return count > self.login_limit_piccode_count

#     def reset_pwd_freeze(self, logincode):
#         client = self.__init_login_redis()
#         client.delete(self.AUTH_LOGIN_PWD_ERROR_KEY.format(logincode))

#     # ----------------------------------------------
#     #        ip address limit
#     # ----------------------------------------------

#     def is_login_ip_error_limit(self, remove_ip):
#         rkey = self.AUTH_LOGIN_IP_ERROR_KEY.format(remove_ip)

#         client = self.__init_login_redis()
#         count = self.__redis_apis.incr_expire(
#             client, rkey, self.login_ip_freeze_timeout)
#         return count > self.login_ip_freeze_count
