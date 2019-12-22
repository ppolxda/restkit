# -*- coding: utf-8 -*-
"""
@create: 2017-10-26 14:13:49.

@author: name

@desc: sys_restful_handler
"""
import os
import six
import json
import uuid
import copy
import time
import codecs
import hashlib
import datetime
import pkg_resources
from restkit import rest
from restkit.rest import http_app
from tornado.template import Template
from restkit.handlers.http_mrg_conns.http_base import HttpBaseHandler
from restkit.tools.field_checker import FeildCheck
from restkit.tools.field_checker import FeildOption
from restkit.tools.error_info import _N
from restkit.tools.error_info import _
from restkit.tools.error_info import error_info
from restkit.tools.error_info import TextString
# from .sys_restful_id import PARENT_PATH_NAME
# from .sys_restful_id import PARENT_API_KEY
# from .sys_restful_id import ROOT_PATH_NAME

DEFAULT_LANG = "en-US,en;q=0.9"
FPATH = os.path.abspath(os.path.dirname(__file__))
PARENT_SUB_ENV_NAME = "{name}Env({prefix_url})"
BASE_CONFIG_JSON = {
    "_type": "export",
    "__export_format": 3,
    "__export_date": "2017-10-30T06:59:46.538Z",
    "__export_source": "insomnia.desktop.app:v5.9.6",
    "resources": [
        {
            "_id": '__WORKSPACE_ID__',
            "parentId": None,
            "modified": 1509346642900,
            "created": 1509346642900,
            # "name": PARENT_PATH_NAME,
            "description": "",
            "certificates": [],
            "_type": "workspace"
        },
        # {
        #     # "_id": '__BASE_ENVIRONMENT_ID__',
        #     # "parentId": '__WORKSPACE_ID__',
        #     "modified": 1509346642913,
        #     "created": 1509346642913,
        #     "name": "Base Environment",
        #     "data": {},
        #     "color": None,
        #     "isPrivate": False,
        #     "_type": "environment"
        # },
        {
            "_id": '__FOLDER_1__',
            "parentId": '__WORKSPACE_ID__',
            "modified": 1509346676859,
            "created": 1509346676859,
            # "name": ROOT_PATH_NAME,
            "description": "",
            "environment": {},
            "metaSortKey": -1509346676859,
            "_type": "request_group"
        }
        # {
        #     "_id": "jar_638250e9bcd14096abe3a6f4e64f431f",
        #     "parentId": "wrk_d6652a95a1c54f3489a507f96308c360",
        #     "modified": 1509346642907,
        #     "created": 1509346642907,
        #     "name": "Default Jar",
        #     "cookies": [],
        #     "_type": "cookie_jar"
        # },
    ]
}


@http_app.route()
class HttpRestfulClientHandler(HttpBaseHandler):

    @staticmethod
    def mktime():
        return int(time.time() * 1000)

    @staticmethod
    def uuid():
        return str(str(uuid.uuid4())).replace('-', '').replace('_', '')

    def md5(self, pid, val):
        if isinstance(pid, TextString):
            lang = self.get_language()
            pid = pid.to_string(lang)

        if isinstance(val, TextString):
            lang = self.get_language()
            val = val.to_string(lang)

        val = pid + val
        data = hashlib.md5(val.encode('utf8'))
        return data.hexdigest()

    def make_url(self, url, parames=None, ishost=False):
        is_full_url = self.get_argument('is_full_url', False)
        vkey = self.get_argument('vkey', self.gsettings.PARENT_API_KEY)
        if ishost is False and vkey != 'disable' and not is_full_url:
            return '{{%s}}%s' % (vkey, url)

        domain = self.get_argument('domain', None)
        if domain == 'localhost':
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

    def loop_path(self, fpath):
        if not fpath:
            raise Exception('fpath null')

        if isinstance(fpath, TextString):
            lang = self.get_language()
            fpath = fpath.to_string(lang)

        if fpath[0] == '/':
            fpath = fpath[1:]

        _paths = fpath.split('/')
        _prev_path = 'root'

        while _paths:
            _path_name = _paths.pop(0)
            _cur_path = _prev_path + '/' + _path_name

            yield _prev_path, _cur_path, _path_name, len(_paths) <= 0
            _prev_path = _cur_path

    @staticmethod
    def markdown_fields(fields):
        assert isinstance(fields, (dict, list))
        # _fields = [
        #     ['name', 'type', 'must', 'default', 'memo', 'other'],
        #     [':---', ':--:', ':--:', ':---', ':---', ':---']
        # ]

        _fields = []
        if isinstance(fields, list):
            # [{'name': 'logincode', 'value': 'system', 'desc': _('Account')}]
            for val in fields:
                _fields.append([
                    val['name'], 'string', 'true',
                    val['value'], val.get('desc', '')
                ])
        else:
            for key, val in fields.items():
                options = val.get('options', {})
                _fields.append([
                    key, val['type'],
                    str(val.get('optional', False)),
                    str(val.get('default', '')),
                    val.get('comment', ''),
                    ','.join(['{}={}'.format(k, v) if k != 'memo' else v
                              for k, v in options.items()
                              if v is not None and v != 'none' and
                              k not in ['update', 'key', 'inc', 'default']])
                ])

        return '\n'.join(['|'.join(i) for i in _fields])

    @rest.get(api_key='sys_restful_clinet[GET]',
              path='/devel/rest_json', data_types=[],
              rest_path=_N('/').join([_('1.Development and debugging'),
                                      _('Insomnia Client Config')]),
              need_logged=False, is_debug=True, print_rsp=False,
              query=[
                  {'name': 'lang', 'value': 'en', 'desc': _('Config language')},  # noqa
                  {'name': 'domain', 'value': '', 'desc': _('Domain')},  # noqa
                  {'name': 'nginx_uri', 'value': '', 'desc': _('Nginx_uri')},  # noqa
                  {'name': 'ssh_tag', 'value': '', 'desc': _('Ssh_tag(http|https)')},  # noqa
                  {'name': 'vkey', 'value': '', 'desc': _('Env Key(disable:use full url config)')},  # noqa
                  {'name': 'workspace_name', 'value': '', 'desc': _('Output Config Pathname')},  # noqa
                  {'name': 'project_name', 'value': '', 'desc': _('Output Config ProjectName')},  # noqa
                #   {'name': 'pathenvjson', 'value': '{}', 'desc': _('Output Config Base Env Config')},  # noqa
                  {'name': 'nogenenv', 'value': '', 'desc': _('Output Config generate Env Config')},  # noqa
              ])
    def get_config(self, *args, **kwargs):  # noqa
        finish_path = []
        lang = self.get_argument('lang', DEFAULT_LANG)
        self.set_header('Accept-Language', lang)

        handles = [
            handle for handle in http_app.http_handler
            if handle[2]['rest_option'].kwargs.get('rest_path', None)
        ]

        handle_rest_path = {
            TextString.t_string(
                lang, handle[2]['rest_option'].kwargs.get('rest_path')
            ): handle
            for handle in handles
        }

        file_format = 'fld_{0}'
        req_format = 'req_{0}'
        pair_format = 'pair_{0}'
        env_format = 'env_{0}'
        project_name = self.get_argument(
            'project_name', self.gsettings.ROOT_PATH_NAME.to_string(lang)
        )
        projectid = file_format.format(self.md5('groupid', project_name))

        rest_paths = set()
        for rest_path in handle_rest_path:
            handle = handle_rest_path[rest_path]
            api_key = handle[2]['api_key']
            rest_option = handle[2]['rest_option']
            requert_parames = getattr(handle[1], 'requert_parames_config', {})
            response_parames = getattr(handle[1], 'response_parames_config', {})  # noqa
            requert_parames = self.json_serial_reload(requert_parames)
            response_parames = self.json_serial_reload(response_parames)

            # check duplicate
            if rest_path in rest_paths:
                return self.send_error(
                    10001, reason='rest path duplicate[{}][{}]'.format(
                        rest_path, api_key))

            rest_paths.add(rest_path)

            do_end_path = {}
            for _prev_path, _cur_path, _path_name, _is_last in self.loop_path(rest_path):  # noqa
                if _cur_path in do_end_path:
                    continue

                mktime = self.mktime()
                method = rest_option.method
                kwargs = self.json_serial_reload(rest_option.kwargs)
                metasortkey = '[{}]{}'.format(method, rest_path)
                query_parames = kwargs.get('query', [])
                params_req_list = requert_parames.get(api_key, {})
                params_rsp_list = response_parames.get(api_key, {})
                params_rsp_list.update({
                    'error': FeildOption('string', _('Error code'), '0', maxlen=10, minlen=1).to_dict(),  # noqa
                    'error_text': FeildOption('string', _('Error desc'), '0', maxlen=256, minlen=1).to_dict()  # noqa
                })
                params_req_list = self.json_serial_reload({
                    key: val.to_dict() if isinstance(val, FeildOption)
                    else val for key, val in params_req_list.items()
                })
                params_rsp_list = self.json_serial_reload({
                    key: val.to_dict() if isinstance(val, FeildOption)
                    else val for key, val in params_rsp_list.items()
                })
                params_list = {
                    key: FeildCheck.field_defval(
                        key, val['type'], val.get('default', '')
                    )
                    for key, val in params_req_list.items()
                }
                mdpath = FPATH + '/sys_restful_doc.md'
                with codecs.open(mdpath, encoding='utf8') as fs:
                    tmpl = fs.read()

                tmpl = Template(tmpl)
                description = tmpl.generate(
                    path=rest_option.path,
                    desc=kwargs.get('desc', 'api desc'),
                    method=method,
                    api_key=api_key,
                    query_parames=self.markdown_fields(query_parames),
                    req_parames=self.markdown_fields(params_req_list),
                    rsp_parames=self.markdown_fields(params_rsp_list),
                    req_json_parames=self.json_dumps(params_req_list,
                                                     indent=4, sort_keys=False,
                                                     ensure_ascii=False,
                                                     default=self.json_serial),
                    rsp_json_parames=self.json_dumps(params_rsp_list,
                                                     indent=4, sort_keys=False,
                                                     ensure_ascii=False,
                                                     default=self.json_serial),
                    query_json_parames=self.json_dumps({
                        'cnname_define': kwargs.get(
                            'query_define', {}
                        ).get('cnname_define', {}),
                        'options_define': kwargs.get(
                            'query_define', {}
                        ).get('options_define', {})
                    }, indent=4, sort_keys=False, ensure_ascii=False,
                        default=self.json_serial)
                ).decode('utf8')

                if _prev_path in do_end_path:
                    parentid = do_end_path[_prev_path]['_id']
                else:
                    parentid = projectid

                if not _is_last:
                    define = {
                        "_id": file_format.format(
                            self.md5(projectid, _cur_path)),
                        "parentId": parentid,
                        "modified": mktime,
                        "created": mktime,
                        "name": _path_name,
                        "description": 'path',
                        "environment": kwargs.get('env', {}),
                        "metaSortKey": '[{}]{}'.format('PATH', rest_path),
                        "_type": "request_group"
                    }
                    # result_dict[path] = define
                elif method == 'GET' and \
                        not kwargs.get('is_urlencoded', False):
                    define = {
                        "_id": file_format.format(
                            self.md5(projectid, rest_path)),
                        "parentId": parentid,
                        "modified": mktime,
                        "created": mktime,
                        "url": self.make_url(rest_option.path),
                        "name": _path_name,
                        "description": description,
                        "method": method,
                        "body": {
                            "mimeType": "application/x-www-form-urlencoded",
                            "params": [
                                {
                                    "name": "where",
                                    "value": self.json_dumps(
                                        params_list,
                                        indent=4,
                                        sort_keys=False,
                                        ensure_ascii=False
                                    ),
                                    "id": pair_format.format(self.uuid()),
                                    "disabled": False
                                },
                                {
                                    "name": "page",
                                    "value": self.json_dumps([0, 50]),
                                    "id": pair_format.format(self.uuid()),
                                    "disabled": False
                                },
                                {
                                    "name": "sort",
                                    "value": self.json_dumps({}),
                                    "id": pair_format.format(self.uuid()),
                                    "disabled": False
                                }
                            ]
                        },
                        "parameters": query_parames,
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "application/x-www-form-urlencoded",
                                "id": pair_format.format(self.uuid())
                            },
                            {
                                "name": "Accept-Language",
                                "value": "{{lang}}",
                                "id": pair_format.format(self.uuid())
                            }
                        ],
                        "authentication": {},
                        "metaSortKey": metasortkey,
                        "settingStoreCookies": True,
                        "settingSendCookies": True,
                        "settingDisableRenderRequestBody": False,
                        "settingEncodeUrl": True,
                        "_type": "request"
                    }
                elif method == 'POST' and \
                        kwargs.get('is_csv', False):
                    define = {
                        "_id": file_format.format(
                            self.md5(projectid, rest_path)),
                        "parentId": parentid,
                        "modified": mktime,
                        "created": mktime,
                        "url": self.make_url(rest_option.path),
                        "name": _path_name,
                        "description": description,
                        "method": method,
                        "body": {
                            "mimeType": "application/json",
                            "text": self.json_dumps(
                                {
                                    "where": params_list,
                                    "page": [0, 50],
                                    "sort": {},
                                    "csv": {
                                        'csvname': 'name',
                                        'csvdesc': 'desc',
                                        'sopt': []
                                    }
                                },
                                indent=4,
                                sort_keys=False,
                                ensure_ascii=False
                            ),
                            # "params": [
                            #     {
                            #         "name": "where",
                            #         "value": self.json_dumps(
                            #             params_list,
                            #             indent=4,
                            #             sort_keys=False,
                            #             ensure_ascii=False
                            #         ),
                            #         "id": pair_format.format(self.uuid()),
                            #         "disabled": False
                            #     },
                            #     {
                            #         "name": "page",
                            #         "value": self.json_dumps([0, 50]),
                            #         "id": pair_format.format(self.uuid()),
                            #         "disabled": False
                            #     },
                            #     {
                            #         "name": "sort",
                            #         "value": self.json_dumps({}),
                            #         "id": pair_format.format(self.uuid()),
                            #         "disabled": False
                            #     },
                            #     {
                            #         "name": "csv",
                            #         "value": self.json_dumps({
                            #             'csvname': 'name',
                            #             'csvdesc': 'desc',
                            #         }),
                            #         "id": pair_format.format(self.uuid()),
                            #         "disabled": False
                            #     }
                            # ]
                        },
                        "parameters": query_parames,
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "application/json",
                                # "value": "application/x-www-form-urlencoded",
                                "id": pair_format.format(self.uuid())
                            },
                            {
                                "name": "Accept-Language",
                                "value": "{{lang}}",
                                "id": pair_format.format(self.uuid())
                            }
                        ],
                        "authentication": {},
                        "metaSortKey": metasortkey,
                        "settingStoreCookies": True,
                        "settingSendCookies": True,
                        "settingDisableRenderRequestBody": False,
                        "settingEncodeUrl": True,
                        "_type": "request"
                    }
                elif method == 'POST' and \
                        getattr(rest_option, 'is_file_upload', False):
                    define = {
                        "_id": req_format.format(
                            self.md5(projectid, rest_path)),
                        "parentId": parentid,
                        "modified": mktime,
                        "created": mktime,
                        "url": self.make_url(rest_option.path),
                        "name": _path_name,
                        "description": description,
                        "method": method,
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "multipart/form-data",
                                "id": pair_format.format(self.uuid())
                            },
                            {
                                "name": "Accept-Language",
                                "value": "{{lang}}",
                                "id": pair_format.format(self.uuid())
                            }
                        ],
                        "body": {
                            "mimeType": "multipart/form-data",
                            "params": [
                                {
                                    "disabled": False,
                                    "fileName": '',
                                    "id": pair_format.format(self.uuid()),
                                    "name": 'files',
                                    "type": "file",
                                    "value": ""
                                }
                            ],
                        },
                        "parameters": query_parames,
                        "authentication": {},
                        "metaSortKey": metasortkey,
                        "settingStoreCookies": True,
                        "settingSendCookies": True,
                        "settingDisableRenderRequestBody": False,
                        "settingEncodeUrl": True,
                        "_type": "request"
                    }
                else:
                    if not kwargs.get('is_urlencoded', False):
                        body = {
                            "mimeType": "application/json",
                            "text": self.json_dumps(
                                params_list,
                                indent=4,
                                sort_keys=False,
                                ensure_ascii=False
                            )
                        }
                        headers = [
                            {
                                "name": "Content-Type",
                                "value": "application/json",
                                "id": pair_format.format(self.uuid())
                            },
                            {
                                "name": "Accept-Language",
                                "value": "{{lang}}",
                                "id": pair_format.format(self.uuid())
                            }
                        ]
                    else:
                        body = {
                            "mimeType": "application/x-www-form-urlencoded",
                            "params": [
                                {
                                    "id": pair_format.format(self.uuid()),
                                    "name": key,
                                    "value": val
                                }
                                for key, val in params_list.items()
                            ],
                        }
                        headers = [
                            {
                                "name": "Content-Type",
                                "value": "application/x-www-form-urlencoded",
                                "id": pair_format.format(self.uuid())
                            },
                            {
                                "name": "Accept-Language",
                                "value": "{{lang}}",
                                "id": pair_format.format(self.uuid())
                            }
                        ]

                    define = {
                        "_id": req_format.format(
                            self.md5(projectid, rest_path)),
                        "parentId": parentid,
                        "modified": mktime,
                        "created": mktime,
                        "url": self.make_url(rest_option.path),
                        "name": _path_name,
                        "description": description,
                        "method": method,
                        "body": body,
                        "headers": headers,
                        "parameters": query_parames,
                        "authentication": {},
                        "metaSortKey": metasortkey,
                        "settingStoreCookies": True,
                        "settingSendCookies": True,
                        "settingDisableRenderRequestBody": False,
                        "settingEncodeUrl": True,
                        "_type": "request"
                    }

                if kwargs.get('need_bearer_token', False):
                    define["authentication"] = {
                        "token": "access_token",
                        "type": "bearer"
                    }

                if kwargs.get('is_oauth2_authcode', False):
                    define["authentication"] = {
                        "accessTokenUrl": self.make_url(kwargs.get('token_url', '')),  # noqa
                        "authorizationUrl": self.make_url(kwargs.get('auth_url', '')),  # noqa
                        "clientId": "appkey",
                        "clientSecret": "appsecret",
                        "grantType": "authorization_code",
                        "scope": kwargs.get('scope_key', ''),
                        "redirectUrl": "http://localhost:8888/test",
                        "type": "oauth2"
                    }

                if kwargs.get('is_base_auth', False):
                    define["authentication"] = {
                        "disabled": False,
                        "password": "test",
                        "type": "basic",
                        "username": "test"
                    }

                # if kwargs.get('is_oauth2_passwot', False):
                #     define["authentication"] = {
                #         "accessTokenUrl": "http://192.168.1.24:10100/users/oauth/auth5",  # noqa
                #         "authorizationUrl": "http://192.168.1.24:10100/users/oauth/auth",  # noqa
                #         "clientId": "clientId",
                #         "clientSecret": "clientSecret",
                #         "grantType": "password",
                #         "redirectUrl": "http://192.168.1.24:10100/users",
                #         "type": "oauth2"
                #     }

                do_end_path[_cur_path] = define
                finish_path.append(define)

        base_json = copy.deepcopy(BASE_CONFIG_JSON)
        base_json['__export_date'] = str(datetime.datetime.now())
        base_json['resources'] += finish_path
        prefix_url = self.make_url('', ishost=True)
        env_name = PARENT_SUB_ENV_NAME.format(
            name=self.gsettings.ROOT_PATH_NAME.to_string(lang),
            prefix_url=prefix_url
        )

        vkey = self.get_argument('vkey', self.gsettings.PARENT_API_KEY)
        nogenenv = self.get_argument('nogenenv', None)
        if vkey != 'disable' and nogenenv is None:
            base_json['resources'].append({
                "_id": env_format.format(
                    self.md5(projectid, env_name)
                ),
                "parentId": '__BASE_ENVIRONMENT_ID__',
                "modified": mktime,
                "created": mktime,
                "name": env_name,
                "data": {
                    vkey: prefix_url,
                    "lang": lang
                },
                "color": None,
                "isPrivate": False,
                "_type": "environment"
            })

        workspace_name = self.get_argument(
            'workspace_name', self.gsettings.PARENT_PATH_NAME.to_string(lang)
        )
        project_name = self.get_argument(
            'project_name', self.gsettings.ROOT_PATH_NAME.to_string(lang)
        )
        base_json['resources'][0]['name'] = workspace_name
        base_json['resources'][1]['name'] = project_name
        base_json['resources'][1]['_id'] = projectid

        # pathenvjson = self.get_argument('pathenvjson', None)
        # if pathenvjson is not None:
        #     try:
        #         pathenvjson = self.json_loads(pathenvjson)
        #     except Exception:
        #         pass
        #     else:
        #         base_json['resources'][1]['data'] = pathenvjson

        self.write(self.json_dumps(
            base_json,
            indent=4, sort_keys=False,
            ensure_ascii=False,
            default=self.json_serial)
        )
