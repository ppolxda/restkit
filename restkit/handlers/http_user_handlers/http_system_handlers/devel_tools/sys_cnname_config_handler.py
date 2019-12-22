# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:13:49.

@author: name

@desc: sys_cnname_config_handler
"""
import json
import uuid
import time
import hashlib
from restkit import rest
from restkit.rest import http_app
from restkit.handlers.http_user_conns.http_base import HttpBaseHandler
from restkit.tools.error_info import _N
from restkit.tools.error_info import _
from .sys_restful_handler import DEFAULT_LANG


@http_app.route()
class HttpGetConfigClientHandler(HttpBaseHandler):

    @staticmethod
    def mktime():
        return int(time.time() * 1000)

    @staticmethod
    def uuid():
        return str(str(uuid.uuid4())).replace('-', '').replace('_', '')

    @staticmethod
    def md5(val):
        data = hashlib.md5(val.encode('utf8'))
        return data.hexdigest()

    @rest.get(api_key='sys_cnname_clinet[GET]',
              path='/devel/cnname_json', data_types=[],
              rest_path=_N('/').join([_('1.Development and debugging'),
                                      _('Cnname Config')]),
              need_logged=False, is_debug=True, print_rsp=False)
    def get_config(self, *args, **kwargs):
        lang = self.get_argument('lang', DEFAULT_LANG)
        self.set_header('Accept-Language', lang)

        handles = [
            handle[2] for handle in http_app.http_handler
            if handle[2]['rest_option'].kwargs.get('rest_path', None) is not None and  # noqa
            handle[2]['rest_option'].method == 'GET' and
            handle[2]['rest_option'].kwargs.get('query_define', None) is not None  # noqa
        ]

        base_json = {
            handle['rest_option'].api_key:
            handle['rest_option'].kwargs['query_define'].get(
                'cnname_define', {})
            for handle in handles
        }

        self.write(json.dumps(base_json,
                              indent=4, sort_keys=False, ensure_ascii=False))
