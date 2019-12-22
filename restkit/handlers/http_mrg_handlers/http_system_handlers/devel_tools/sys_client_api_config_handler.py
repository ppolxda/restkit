# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:13:49.

@author: name

@desc: sys_client_api_config_handler
"""
import json
from restkit import rest
from restkit.rest import http_app
from restkit.handlers.http_mrg_conns.http_base import HttpBaseHandler
from restkit.tools.field_checker import FeildOption
from restkit.tools.error_info import _N
from restkit.tools.error_info import _
from .sys_restful_handler import DEFAULT_LANG


@http_app.route()
class HttpApiConfigClientHandler(HttpBaseHandler):

    def make_url(self, url, parames=None):
        is_local = self.get_argument('is_local', False)
        domain = self.get_argument('domain', None)
        if is_local:
            return self.gsettings.format_url(
                self.gsettings.use_ssh_tag,
                'localhost:{}'.format(self.gsettings.listen_port),
                '', url, parames
            )
        elif domain:
            nginx_uri = self.get_argument('nginx_uri', '')
            ssh_tag = self.get_argument('ssh_tag', 'http')
            return self.gsettings.format_url(
                ssh_tag, domain,
                nginx_uri, url, parames
            )
        else:
            return http_app.make_url(url, parames)

    @rest.get(api_key='sys_client_api_config[GET]',
              path='/devel/client_api_config_json', data_types=[],
              rest_path=_N('/').join([_('1.Development and debugging'),
                                      _('Client Api Config')]),
              need_logged=False, is_debug=True, print_rsp=False)
    def get_config(self):
        lang = self.get_argument('lang', DEFAULT_LANG)
        self.set_header('Accept-Language', lang)

        handles = [
            handle for handle in http_app.http_handler
            if handle[2]['rest_option'].kwargs.get('rest_path', None) is not None  # noqa
        ]

        base_json = {}
        for handle in handles:
            requert_parames = getattr(handle[1], 'requert_parames_config', {})
            response_parames = getattr(handle[1], 'response_parames_config', {})  # noqa
            handle = handle[2]
            rest_option = handle['rest_option']

            method = rest_option.method
            api_key = rest_option.api_key
            params_req_list = requert_parames.get(api_key, {})
            params_rsp_list = response_parames.get(api_key, {})
            params_rsp_list.update({
                'error': FeildOption('string', _('error code'), '0', maxlen=10, minlen=1).to_dict(),  # noqa
                'error_text': FeildOption('string', _('error desc'), '0', maxlen=256, minlen=1).to_dict()  # noqa
            })
            params_req_list = {
                key: val.to_dict() if isinstance(val, FeildOption)
                else val for key, val in params_req_list.items()}
            params_rsp_list = {
                key: val.to_dict() if isinstance(val, FeildOption)
                else val for key, val in params_rsp_list.items()}
            assert api_key.count('[') == 1 and api_key.endswith(']')

            if method == 'GET' and \
                    rest_option.kwargs.get('query_define', None) is None:
                continue

            base_json[api_key.replace('[', '_').replace(']', '').lower()] = {
                'api_key': api_key,
                'api_url': self.make_url(rest_option.path),
                'api_uri': rest_option.path,
                'nginx_uri': self.gsettings.nginx_uri,
                'rest_path': rest_option.kwargs.get('rest_path', ''),
                'fields': params_req_list,
                'fields_rsp': params_rsp_list,
                'method': method,
                'is_debug': rest_option.kwargs.get('is_debug', False),  # noqa
                'api_key_check': rest_option.kwargs.get('api_key_check', False),  # noqa
                'is_csv': rest_option.kwargs.get('is_csv', False),
                'query_fields': rest_option.kwargs.get('query', ''),
                'desc': rest_option.kwargs.get('desc', ''),
                'resfmt': rest_option.kwargs.get('resfmt', ''),
                'options_define': rest_option.kwargs.get(
                    'query_define', {}).get('options_define', {}),
                'cnname_define': rest_option.kwargs.get(
                    'query_define', {}).get('cnname_define', {})
            }

        self.write(self.json_dumps(
            base_json,
            indent=4, sort_keys=False, ensure_ascii=False
        ))
