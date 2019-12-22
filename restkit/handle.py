# -*- coding: utf-8 -*-
"""
Created on 2019-10-15 15:50:38.

@author: name
"""
from __future__ import absolute_import, division, print_function
import re
import json
import base64
import datetime
import logging
import traceback
from tornado import gen
from tornado import web
# from tornado import httputil
from restkit.tools.string_unit import decode_str

try:
    from urllib.parse import urlencode, unquote
except ImportError:
    from urllib import urlencode, unquote


LOGGER_LOG = logging.getLogger('restkit')


class HttpHandleOption(object):
    """HttpHandleOption."""
    HANDLER_REGIX = re.compile(r'^.*?Handler$')

    def __init__(self, route, uri, permission, **kwargs):
        self.uri = uri
        self.permission = permission
        self.route = route

        for _k, _v in kwargs.items():
            setattr(self, _k, _v)

    @property
    def use_ssh_tag(self):
        return self.route.use_ssh_tag

    @property
    def domain(self):
        return self.route.domain

    @property
    def nginx_uri(self):
        return self.route.nginx_uri

    @property
    def full_url(self):
        return '{0}://{1}'.format(
            'https' if self.use_ssh_tag else 'http', self.domain
        ) + self.nginx_uri + self.uri

    def permission_key(self, handler):
        assert isinstance(handler, web.RequestHandler)
        return '{}[{}]'.format(self.permission, handler.request.method)


def logger_requert(write_log=True, print_rsp=True):
    def func_wrapper(func):
        @gen.coroutine
        def wrapper(self, *args, **kwargs):
            start_time = datetime.datetime.now()
            try:
                yield func(self, *args, **kwargs)
            except Exception:
                LOGGER_LOG.warn(traceback.format_exc())
            finally:
                if write_log:
                    if print_rsp:
                        LOGGER_LOG.debug(
                            "%d %s <req:%s><rsp:%s><location:%s> %s ms",
                            self.get_status(),
                            self._request_summary(),
                            decode_str(self.request.body),
                            self._write_buffer,
                            self._headers.get("Location"),
                            (datetime.datetime.now() -
                             start_time).microseconds / 1000.0
                        )
                    else:
                        LOGGER_LOG.debug(
                            "%d %s <req:%s><rsp:%s><location:%s> %s ms",
                            self.get_status(),
                            self._request_summary(),
                            decode_str(self.request.body),
                            '',
                            self._headers.get("Location"),
                            (datetime.datetime.now() -
                             start_time).microseconds / 1000.0
                        )

                if hasattr(self, 'mysql_rollback'):
                    yield getattr(self, 'mysql_rollback')()
        return wrapper
    return func_wrapper


class HttpRequestHandler(web.RequestHandler):
    """HttpRequestHandler."""

    def __init__(self, *args, **kwargs):
        super(HttpRequestHandler, self).__init__(*args, **kwargs)

    def initialize(self, **kwargs):  # pylint: disable=I0011,W0221
        self.route_option = kwargs.get('route_option', None)

    def get_remove_ip(self):
        return self.request.headers.get(
            'X-Forwarded-For', self.request.headers.get(
                'X-Real-Ip', self.request.remote_ip
            )
        )

    @property
    def permission_key(self):
        assert isinstance(self.route_option, HttpHandleOption)
        return self.route_option.permission_key(self)

    @staticmethod
    def json_base64_encode(text):
        """json=>b64encode."""
        return base64.b64encode(json.dumps(text))

    @staticmethod
    def json_base64_decode(text):
        """b64decode=>json."""
        return json.loads(base64.b64decode(text))

    def decode_json_from_body(self):
        """b64decode=>json."""
        if self.request.body:
            return json.loads(self.request.body)
        else:
            return {}

    # ----------------------------------------------
    #        dict
    # ----------------------------------------------

    def arguments2dict(self):
        def get_field(val):
            try:
                return val[0]
            except IndexError:
                return val

        return {
            key: get_field(val)
            for key, val in self.request.body_arguments.items()
        }

    def dict2arguments(self, _dict_data):
        """dict2arguments."""
        return urlencode(_dict_data)

    def write_encode(self, chunk):
        """write_encode."""
        chunk = self.dict2arguments(chunk)
        self.write(chunk)
