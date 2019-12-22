# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:13:49.

@author: name

@desc: sys_sign_handler
"""
from tornado import gen
from tornado.web import HTTPError
from restkit import rest
from restkit.rest import http_app
from restkit.handlers.http_mrg_conns.http_base import HttpBaseHandler
from restkit.tools.field_checker import parames_config_dict
from restkit.tools.error_info import _N
from restkit.tools.error_info import _
from restkit.tools.error_info import error_info
from restkit.tools.field_checker import FeildCheck

field_check = FeildCheck.field_check
# QUERY_DEFINE = user_otp_binding_user_status_query_sql.QUERY_DEFINE


@http_app.route()
class HttpLoginNeedPicCodeHandler(HttpBaseHandler):

    requert_parames_config = {
        'sys_sign_test[POST]': {
            'logincode': parames_config_dict('string', _('account'), 'system', maxlen=32, minlen=6),  # noqa
        }
    }

    @rest.post(api_key='sys_sign_test[POST]',
               path='/devel/sign_test', data_types=[],
               rest_path=_N('/').join([_('1.Development and debugging'),
                                       _('Package Sign')]),
               query_define={},
               is_debug=True, need_signed=False)
    def get_catcha_req(self, *args, **kwargs):
        req_data = self.decode_json_from_body()
        sign = self.sign_json(req_data)
        req_data['sign'] = sign
        self.write_error_json(
            error_info.ERROR_SUCESS,
            req_sign=sign,
            req_data=req_data
        )
