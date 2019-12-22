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
from .apikey_api import is_has_key_by_userid  # noqa
from .apikey_api import is_has_apikey_by_userid  # noqa
from .apikey_api import is_has_apikey_by_roleid  # noqa
from .apikey_api import get_muser_role_by_userid  # noqa


class HttpApiKeyBaseHandler(HttpSessionBaseHandler):

    _session = None

    # def __init__(self, *args, **kwargs):
    #     """__init__."""
    #     super(HttpRequestHandler, self).__init__(*args, **kwargs)

    def initialize(self, **kwargs):  # noqa
        """initialize."""
        super(HttpApiKeyBaseHandler, self).initialize(**kwargs)

    @gen.coroutine
    def rest_initialize(self, api_key, rest_option, *args, **kwargs):
        yield super(HttpApiKeyBaseHandler, self).rest_initialize(
            api_key, rest_option, *args, **kwargs
        )
        self.api_key_check = rest_option.kwargs.get('api_key_check', True)

        result = self.is_has_apikey()
        if not result:
            # self.set_status(401)
            self.write_error_json(error_info.ERROR_API_DISABLE)
            self.finish()
            raise HTTPError(401)

    def is_has_apikey(self):
        if not self.gsettings.apikey_check or \
            not self.need_logged or \
                not self.api_key_check or \
                self.session().logincode == 'system':
            return True

        redis_cli = self.redis_client('user_db')

        result = is_has_key_by_userid(redis_cli, self.session().userid)
        if result:
            if is_has_apikey_by_userid(
                    redis_cli, self.session().userid, self.api_key):
                return True
            else:
                return False

        roleids = get_muser_role_by_userid(redis_cli, self.session().userid)
        if roleids:
            for i in roleids:
                if is_has_apikey_by_roleid(
                        redis_cli, i, self.api_key):
                    return True
                else:
                    return False

        return False
