# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:02:55.

@author: name

@desc: http_base
"""
import os
import six
import json
import time
import base64
import datetime
import decimal
import traceback
import hashlib
import binascii
import logging
from collections import OrderedDict
from tornado import gen
from tornado.web import HTTPError
from restkit.rest import http_app
from restkit.rest import RestHandler
from restkit.handle_redis import RedisHandler
from restkit.handle_database import HttpDBaseHandler
from restkit.transactions import Transaction
from restkit.tools.field_checker import FeildOption
from restkit.tools.mongo_query import QueryParames
from restkit.tools.string_unit import FeildInVaild
from restkit.tools.error_info import error_info
from restkit.tools.error_info import TextString
from restkit.tools.configbase import LoginLimitSettings


try:
    from sqlalchemy.engine import RowProxy
except ImportError:
    RowProxy = dict


IS_DEBUG = bool(os.environ.get('IS_DEBUG', 'false'))


class ErrorFinish(Exception):
    pass


class HttpBaseHandler(RestHandler,
                      RedisHandler,
                      HttpDBaseHandler):

    # def check_origin(self, origin):
    #     return True

    def initialize(self, **kwargs):  # noqa
        """initialize."""
        self.api_key_check = True
        self.need_logged = True
        self.need_signed = True
        self.need_otp_logged = True
        self.product_code = True
        self.product_check = True
        self.is_debug = False
        super(HttpBaseHandler, self).initialize(**kwargs)

    @property
    def logger(self) -> logging.Logger:
        return self.settings['logger']

    @property
    def gsettings(self) -> LoginLimitSettings:
        return self.settings['gsettings']

    @gen.coroutine
    def rest_initialize(self, api_key, rest_option, *args, **kwargs):
        yield super(HttpBaseHandler, self).rest_initialize(
            api_key, rest_option, *args, **kwargs
        )
        self.api_key = api_key
        self.rest_option = rest_option
        self.need_logged = rest_option.kwargs.get('need_logged', True)
        self.need_signed = rest_option.kwargs.get('need_signed', True)
        self.need_otp_logged = rest_option.kwargs.get('need_otp_logged', True)
        self.is_debug = rest_option.kwargs.get('is_debug', False)

        if self.is_debug and not IS_DEBUG:
            raise HTTPError(404)

    @staticmethod
    def is_has_field(dictobj, key):
        assert isinstance(dictobj, dict)
        assert isinstance(key, six.string_types)
        return key in dictobj and dictobj[key] is not None

    def get_remove_ip(self):
        return self.request.headers.get(
            'X-Forwarded-For', self.request.headers.get(
                'X-Real-Ip', self.request.remote_ip
            )
        )

    def get_language(self):
        if "Accept-Language" in self.request.headers:
            languages = self.request.headers["Accept-Language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))

            if locales:
                locales.sort(key=lambda pair: pair[1], reverse=True)
                codes = [l[0] for l in locales]
                return error_info.get_langs(*codes)

        return error_info.default_lang()

    # ----------------------------------------------
    #        signed
    # ----------------------------------------------

    def sign_json(self, data, skey=None):
        if not isinstance(data, dict) or not data:
            return None

        if 'sign' in data:
            data = data.copy()
            data.pop('sign')

        if '@skey' in data:
            data = data.copy()
            skey = data.pop('@skey')

        if not skey:
            skey = self.settings.get('cookie_secret', '')

        if not skey:
            raise TypeError('cookie_secret not set')

        if 'utc' not in data:
            raise TypeError('data invail, utc not set')

        if isinstance(skey, six.string_types):
            skey = six.b(skey)

        keys = list(data.keys())
        keys.sort()

        sdata = '&'.join(
            ['{0}={1}'.format(key, data[key]) for key in keys]
        )

        return binascii.hexlify(hashlib.pbkdf2_hmac(
            'sha256', sdata.encode('utf8'), skey, 1024)
        ).decode('utf8')

    def is_sign_invaild(self, data, sign, skey=None):
        if not isinstance(data, dict) or not data:
            return True

        if not isinstance(sign, six.string_types) or not sign:
            return True

        if 'utc' not in data or \
            not isinstance(data['utc'], six.integer_types) or \
                (time.time() - data['utc']) > self.gsettings.sign_timeout:
            return True

        return sign != self.sign_json(data, skey)

    def decode_json_from_body(self):
        """b64decode=>json."""
        if not self.request.body:
            return {}

        return json.loads(
            self.request.body,
            parse_float=decimal.Decimal,
            object_pairs_hook=OrderedDict
        )

    def base64_or_json_decode(self, data):
        try:
            # data = json.loads(data, parse_float=str, parse_int=str)
            data = json.loads(
                data, parse_float=decimal.Decimal,
                object_pairs_hook=OrderedDict
            )
        except json.JSONDecodeError:
            data = base64.b64decode(data)
            data = json.loads(
                data, parse_float=decimal.Decimal,
                object_pairs_hook=OrderedDict
            )
        else:
            return data

    def get_where_parames_from_json(self):
        where = self.decode_json_from_body()

        _where = where.get('where', {})
        _where = {
            key: val
            for key, val in _where.items()
            if val
        }

        return {
            'where': _where,
            'page': where.get('page', [0, 50]),
            'sort': where.get('sort', {}),
            'csv': where.get('csv', {}),
        }

    def get_where_parames(self):
        where = self.get_argument('where', '{}')
        page = self.get_argument('page', '[0, 50]')
        sort = self.get_argument('sort', '{}')
        csv_parame = self.get_argument('csv', '{}')

        _where = self.base64_or_json_decode(where)
        _where = {
            key: val
            for key, val in _where.items()
            if val
        }

        return {
            'where': _where,
            'page': self.base64_or_json_decode(page),
            'sort': self.base64_or_json_decode(sort),
            'csv': self.base64_or_json_decode(csv_parame),
        }

    def pop_where_key(self, where, key):
        try:
            value = where.pop(key)
        except KeyError:
            value = None

        if value and not isinstance(value, six.string_types):
            self.write_error_json_raise(
                error_info.ERROR_KEY_INVAILD,
                {'key': key}
            )

        return value

    def package_rsp(self, code, text=None, **kwargs):
        # TAG - maybe step language
        if isinstance(code, dict):
            return code

        req_data = {}
        try:
            append_text = kwargs.pop('append_text')
        except KeyError:
            append_text = ''

        if isinstance(text, dict):
            error_text = error_info.error_text(code, **text)
        elif isinstance(text, (six.string_types, TextString)):
            error_text = text
        else:
            error_text = error_info.error_text(code)

        req_data.update({
            'error': code,
            'error_text': error_text + append_text
        })
        req_data.update(kwargs)
        return req_data

    def json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y%m%dT%H%M%S")

        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y%m%d")

        elif isinstance(obj, decimal.Decimal):
            return float(obj)

        elif isinstance(obj, FeildOption):
            return obj.to_dict()

        elif isinstance(obj, TextString):
            return obj.to_string(self.get_language())

        elif isinstance(obj, RowProxy):
            return dict(obj)

        else:
            raise TypeError("Type %s not serializable" % type(obj))

    def json_dumps(self, data, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = self.json_serial
        return json.dumps(data, **kwargs)

    def json_loads(self, data):
        return json.loads(
            data, parse_float=decimal.Decimal,
            object_pairs_hook=OrderedDict
        )

    def json_serial_reload(self, data):
        return self.json_loads(self.json_dumps(data))

    def write_error_json(self, code, text=None, **kwargs):
        req_data = self.package_rsp(code, text, **kwargs)
        self.write(self.json_dumps(req_data))

    def write_error_json_raise(self, code, text=None, **kwargs):
        self.write_error_json(code, text, **kwargs)
        raise ErrorFinish()

    def write(self, data):
        if not isinstance(data, (six.string_types, six.binary_type)):
            data = self.json_dumps(data)
        super(HttpBaseHandler, self).write(data)

    # ----------------------------------------------
    #        filters
    # ----------------------------------------------

    @staticmethod
    def filter_keys(field_dict, filter_keys):
        """filter_keys."""
        assert isinstance(field_dict, dict)
        return {key: val for key, val in field_dict.items()
                if key not in filter_keys}

    @staticmethod
    def filter_whitelist(field_dict, filter_keys):
        """filter_whitelist."""
        assert isinstance(field_dict, dict)
        return {key: val for key, val in field_dict.items()
                if key in filter_keys}

    @gen.coroutine
    def trans_spawn(self, trans):
        assert isinstance(trans, Transaction)
        try:
            yield trans.spawn()
        except HTTPError:
            raise
        except ErrorFinish:
            pass
        except (FeildInVaild, QueryParames) as ex:
            if len(ex.args) == 1 and isinstance(ex.args[0], TextString):
                self.write_error_json(
                    error_info.ERROR_FIELD_CHECK_ERROR,
                    ex.args[0]
                )
            else:
                self.write_error_json(
                    error_info.ERROR_FIELD_CHECK_ERROR,
                    str(ex)
                )
        # except DBError as ex:
        #     except_trac = str(traceback.format_exc())
        #     APP_LOGGER.warning(except_trac)

        #     if IS_DEBUG:
        #         self.write_error_json(
        #             error_info.ERROR_DN_EXCEPT,
        #             append_text='[{}: {}]'.format(type(ex).__name__, str(ex))
        #         )
        #     else:
        #         self.write_error_json(error_info.ERROR_DN_EXCEPT)
        except Exception as ex:
            except_trac = str(traceback.format_exc())
            self.logger.warning(except_trac)

            # if run in pyinstaller
            if IS_DEBUG:
                self.write_error_json(
                    error_info.ERROR_EXCEPTION,
                    '{}[{}]'.format(type(ex).__name__, str(ex))
                )
            else:
                self.write_error_json(error_info.ERROR_EXCEPTION,
                                      {'desc': 'unknown error'})

        # TODO - grpc error
        # grpc._channel._Rendezvous: <_Rendezvous of RPC
        # that terminated with (StatusCode.UNAVAILABLE, Connect Failed)>
        finally:
            try:
                yield self.dbase_rollback()
            except Exception:
                pass
            try:
                yield self.redis_rollback()
            except Exception:
                pass
