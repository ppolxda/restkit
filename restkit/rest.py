# -*- coding: utf-8 -*-
"""
@create: 2019-10-14 19:11:26.

@author: name

@desc: rest
"""

import re
import six
import copy
import inspect
import datetime
import functools
import traceback
import logging
# import tornado.ioloop
from tornado import web
from tornado import gen
from tornado import httpserver
from restkit.tools.string_unit import convert

try:
    from urllib.parse import urlencode
    from urllib.parse import quote
except ImportError:
    from urllib import urlencode
    from urllib import quote


SID_REGIX = re.compile(r'sid=([^&]*)')
SUPPORTED_METHODS = web.RequestHandler.SUPPORTED_METHODS


class IgnoreError(Exception):
    pass


class PyRestfulException(Exception):
    """ Class for PyRestful exceptions """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class RestOptions(object):

    def __init__(self, func, method, api_key, path, data_types, **kwargs):
        assert callable(func)
        assert method in SUPPORTED_METHODS
        assert isinstance(api_key, six.string_types)
        assert isinstance(path, six.string_types)
        assert isinstance(data_types, list)

        self.call_func = func
        self.func_name = func.__name__
        self.func_params = inspect.getargspec(func).args[1:]
        self.data_types = data_types or [str] * len(self.func_params)
        self.service_name = re.findall(r"(?<=/)\w+", path)
        self.service_params = re.findall(r"(?<={)\w+", path)
        self.query_params = re.findall(r"(?<=<)\w+", path)
        self.method = method
        self.path = path
        self.api_key = api_key
        self.kwargs = kwargs
        self.write_log = kwargs.get('write_log', True)
        self.print_rsp = kwargs.get('print_rsp', True)
        self.is_file_upload = kwargs.get('is_file_upload', False)

        # kwargs_mode if kwargs_mode = True, rest_initialize will use kwargs
        # kwargs_mode if kwargs_mode = False, rest_initialize will use args
        self.kwargs_mode = kwargs.get('kwargs_mode', True)

        params_types = self.data_types or \
            [str] * len(self.service_params)

        # If the data_types is not specified, assumes str types for the params
        self.params_types = params_types + \
            [str] * (len(self.service_params) - len(params_types))

    # def __call__(self, *args, **kwargs):
    #     return self.call_func(*args, **kwargs)

    @gen.coroutine
    def __call__(self, *args, **kwargs):
        if gen.is_coroutine_function(self.call_func):
            result = yield self.call_func(*args, **kwargs)
        else:
            result = yield gen.coroutine(self.call_func)(*args, **kwargs)
        raise gen.Return(result)


def method_decorator(method, api_key, path, data_types, **kwparams):
    """Decorator for config a python function like a Rest GET verb."""
    def method_func(func):
        """ RestOptions	"""
        return RestOptions(func, method, api_key, path, data_types, **kwparams)
    return method_func


get = functools.partial(method_decorator, 'GET')
post = functools.partial(method_decorator, 'POST')
put = functools.partial(method_decorator, 'PUT')
delete = functools.partial(method_decorator, 'DELETE')
head = functools.partial(method_decorator, 'HEAD')
patch = functools.partial(method_decorator, 'PATCH')
options = functools.partial(method_decorator, 'OPTIONS')


class RestHandler(web.RequestHandler):

    def initialize(self, **kwargs):
        self.__rest_option = None
        self.__rest_options = None
        self.__http_methods = None
        self.__method_rest_option = None
        self.__write_log = []

    @gen.coroutine
    def rest_initialize(self, api_key, rest_option, *args, **kwargs):
        pass

    @gen.coroutine
    def get(self, *args, **kwargs):
        """Executes get method."""
        yield self._exe('GET')

    @gen.coroutine
    def post(self, *args, **kwargs):
        """Executes post method."""
        yield self._exe('POST')

    @gen.coroutine
    def put(self, *args, **kwargs):
        """Executes put method."""
        yield self._exe('PUT')

    @gen.coroutine
    def delete(self, *args, **kwargs):
        """Executes put method."""
        yield self._exe('DELETE')

    @gen.coroutine
    def head(self, *args, **kwargs):
        """Executes get method."""
        yield self._exe('HEAD')

    @gen.coroutine
    def patch(self, *args, **kwargs):
        """Executes get method."""
        yield self._exe('PATCH')

    @gen.coroutine
    def options(self, *args, **kwargs):
        """Executes get method."""
        yield self._exe('OPTIONS')

    @gen.coroutine
    def _exe(self, method):
        """Executes the python function for the Rest Service."""
        request_path = self.request.path
        path = request_path.split('/')
        services_and_params = list(filter(lambda x: x != '', path))

        # Get all funcion names configured in the class RestHandler
        functions = self.get_rest_options_runtime()

        # Get all http methods configured in the class RestHandler
        http_methods = self.http_methods()

        if method not in http_methods:
            raise web.HTTPError(
                405, 'The service not have %s verb' % method)

        is_do = False
        for operation in functions:
            assert isinstance(operation, RestOptions)
            service_name = operation.service_name
            service_params = operation.service_params

            # If the data_types is not specified,
            # assumes str types for the params
            params_types = operation.params_types

            services_from_request = list(
                filter(lambda x: x in path, service_name))

            sparams_len = len(service_params) + len(service_name)

            # TODO - uri regex is Inaccurate conditions
            if operation.method == self.request.method and \
               service_name == services_from_request and \
               sparams_len == len(services_and_params):
                is_do = True

                try:
                    params_values = self._find_value_of_url(
                        service_name,
                        request_path
                    )
                    params_values += self._find_value_of_arguments(operation)
                    self.__rest_option = operation

                    if operation.kwargs_mode:
                        p_kwargs = self._convert_params_values_dict(
                            service_params, params_values, params_types)

                        yield self.rest_initialize(
                            operation.api_key,
                            operation,
                            **p_kwargs
                        )
                        yield operation(self, **p_kwargs)
                    else:
                        p_values = [self]
                        p_values += self._convert_params_values(
                            params_values, params_types)

                        yield self.rest_initialize(
                            operation.api_key, operation, *p_values)
                        yield operation(*p_values)

                except web.HTTPError as ex:
                    self.set_status(ex.status_code, ex.reason)
                    raise ex
                except IgnoreError:
                    pass
                except Exception:
                    # TODO - logger, http_app is not safe
                    http_app.logger.warn(traceback.format_exc())
                    self.send_error(500)
                    # self.send_error(500, reason=str(detail))

        if not is_do:
            raise web.HTTPError(
                405, 'The service not have %s %s verb' % (method, path)
            )

    @property
    def is_write_log(self):
        return self.__rest_option.write_log

    def _request_summary(self):
        is_write_log = getattr(self, 'is_write_log', True)
        if not is_write_log:
            return super(RestHandler, self)._request_summary()

        uri = self.request.uri
        uri = re.sub(SID_REGIX, '', uri)

        if not self.__rest_option:
            return "%s %s (%s)" % (self.request.method, uri,
                                   self.request.remote_ip)

        if self.__rest_option.is_file_upload:
            return "%s %s (%s) <req:%s><rsp:%s><location:%s>" % (
                self.request.method, uri,
                self.request.remote_ip,
                #  self.request.body,
                '',
                self.__write_log,
                self._headers.get("Location")
            )

        elif not self.__rest_option.print_rsp:
            return "%s %s (%s) <req:%s><rsp:%s><location:%s>" % (
                self.request.method, uri,
                self.request.remote_ip,
                self.request.body,
                '',
                self._headers.get("Location")
            )

        else:
            return "%s %s (%s) <req:%s><rsp:%s><location:%s>" % (
                self.request.method, uri,
                self.request.remote_ip,
                self.request.body,
                self.__write_log,
                self._headers.get("Location")
            )

    def flush(self, *args, **kwargs):
        self.__write_log.extend(self._write_buffer)
        super().flush(*args, **kwargs)

    def _find_value_of_url(self, services, url):
        """ Find the values of path params """
        values_of_query = list()
        i = 0
        url_split = url.split("/")
        values = [item for item in url_split
                  if item not in services and item != '']
        for v in values:
            if v is not None:
                values_of_query.append(v)
                i += 1
        return values_of_query

    def _find_value_of_arguments(self, operation):
        values = []
        if len(self.request.arguments) > 0:
            a = operation.service_params
            b = operation.func_params
            params = [item for item in b if item not in a]
            for p in params:
                if p in self.request.arguments.keys():
                    v = self.request.arguments[p]
                    values.append(v[0])
                else:
                    values.append(None)
        elif len(self.request.arguments) == 0 and\
                len(operation.query_params) > 0:
            values = [None] * (len(operation.func_params) -
                               len(operation.service_params))
        return values

    def _convert_params_values_dict(self,
                                    service_params,
                                    values_list,
                                    params_types):
        """ Converts the values to the specifics types """
        return {a: convert(b, c)
                for a, b, c in zip(service_params, values_list, params_types)}
        # return list(map(lambda x: convert(*x), zip(service_params, values_list, params_types)))  # noqa

    def _convert_params_values(self, values_list, params_types):
        """ Converts the values to the specifics types """
        return list(map(lambda x: convert(*x), zip(values_list, params_types)))  # noqa

    @classmethod
    def get_paths(cls):
        """ Generates the resources from path (uri) to deploy the Rest """
        return list(getattr(cls, op).path for op in dir(cls)
                    if isinstance(getattr(cls, op), RestOptions))

    def get_rest_options_runtime(self):
        """ Generates the resources from path (uri) to deploy the Rest """
        if self.__rest_options is None:
            self.__rest_options = self.get_rest_options()
        return self.__rest_options

    @classmethod
    def get_rest_options(cls):
        """ Generates the resources from path (uri) to deploy the Rest """
        return list(getattr(cls, op) for op in dir(cls)
                    if isinstance(getattr(cls, op), RestOptions))

    def http_methods(self):
        if self.__http_methods is None:
            # Get all funcion names configured in the class RestHandler
            functions = self.get_rest_options_runtime()
            # Get all http methods configured in the class RestHandler
            self.__http_methods = list(map(lambda op: op.method, functions))

        return self.__http_methods

    def get_rest_option(self, method):
        if self.__method_rest_option is None:
            functions = self.get_rest_options_runtime()
            self.__method_rest_option = {op.method: op for op in functions}

        assert method in self.__method_rest_option
        return self.__method_rest_option[method]


class HttpAppLoader(object):
    """HttpAppLoader."""

    HANDLER_REGIX = re.compile(r'^.*?Handler$')

    def __init__(self, **kwargs):
        self.settings = {
            'gzip': True,
            'debug': False
        }
        self.settings.update(kwargs)

        self.app = None
        self.logger_name = 'restkit'
        self.logger = logging.getLogger(self.logger_name)
        self.use_ssh_tag = kwargs.get('use_ssh_tag', False)
        self.domain = kwargs.get('domain', None)
        self.nginx_uri = kwargs.get('nginx_uri', '')
        self.prefix_uri = kwargs.get('prefix_uri', '')
        self.http_handler = []
        self.api_keys = set()
        self.uris = set()
        # TAG - fix uri is same,but handler not same error
        self.uri_handler = {}

    def set_use_ssh_tag(self, use_ssh_tag):
        """set_use_ssh_tag.

        is use ssh
        """
        if not isinstance(use_ssh_tag, bool):
            raise TypeError
        self.use_ssh_tag = use_ssh_tag

    def set_domain(self, domain):
        """set_domain."""
        if not isinstance(domain, six.string_types):
            raise TypeError
        self.domain = domain

    def set_nginx_uri(self, nginx_uri):
        """set_nginx_uri."""
        if not isinstance(nginx_uri, six.string_types):
            raise TypeError
        self.nginx_uri = nginx_uri

    def set_prefix_uri(self, prefix_uri):
        """set_prefix_uri."""
        if not isinstance(prefix_uri, six.string_types):
            raise TypeError
        self.prefix_uri = prefix_uri

    def set_logger_name(self, logger_name):
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)

    def handler_log(self, handler):
        if handler.get_status() < 400:
            log_method = self.logger.info
        elif handler.get_status() < 500:
            log_method = self.logger.warning
        else:
            log_method = self.logger.error

        request_time = 1000.0 * handler.request.request_time()
        log_method(
            "%d %s %.2fms",
            handler.get_status(),
            handler._request_summary(),
            request_time,
        )

    def _generate_rest_services(self, rest, **kwargs):
        svs = []
        paths = rest.get_rest_options()
        for option in paths:
            substr = re.sub(
                r"(?<={)\w+}",
                r"[0-9A-Za-z-\.@:%_\+~#=]*?",
                option.path
            ).replace("{", "")
            subpath = re.sub(r"(?<=<)\w+", "", substr).replace("<", "")\
                .replace(">", "")\
                .replace("&", "")\
                .replace("?", "")

            kwargs = copy.deepcopy(kwargs)
            kwargs['api_key'] = option.api_key
            kwargs['rest_option'] = option
            svs.append((subpath, rest, kwargs))

        return svs

    def _add_api_key(self, val):
        assert val not in self.api_keys
        self.api_keys.add(val)

    def _add_uri(self, method, val):
        key = '{}_{}'.format(method, val)

        assert key not in self.uris
        self.uris.add(key)

    def _add_uri_handle(self, uri, module):
        if uri not in self.uri_handler:
            self.uri_handler[uri] = module
            return

        # TAG - fix uri is same,but handler not same error
        error_t = 'uri_handler error uri[{}] module[{}]'.format(uri, module)
        assert self.uri_handler[uri] == module, error_t

    def route(self, **kwargs):
        """route decorator."""
        # cache uri config
        def decorator(handler):
            handlers = self._generate_rest_services(handler, **kwargs)
            for key in handlers:
                self._add_uri(key[2]['rest_option'].method, key[0])
                self._add_api_key(key[2]['api_key'])
                self._add_uri_handle(key[0], key[1].__module__)

            self.http_handler += handlers

            # if self.app is not None:
            #     # '.*$'
            #     self.app.add_handlers(
            #         self.domain.replace('.', '\\.'), handlers)
            return handler
        return decorator

    def listen(self, listen_port, **settings):
        if self.app is not None:
            return

        handles = []
        handles.extend(self.http_handler)

        try:
            ssl_options = settings.pop('ssl_options')
        except KeyError:
            ssl_options = None

        self.settings.update(settings)
        self.settings['log_function'] = self.handler_log
        self.app = web.Application(handles, **self.settings)
        http_server = httpserver.HTTPServer(self.app, ssl_options=ssl_options)

        if self.domain is None:
            self.domain = 'localhost:{}'.format(listen_port)

        http_server.listen(listen_port)

    def make_url(self, url, parames=None):
        """make_url."""
        ssh_tag = 'https' if self.use_ssh_tag else 'http'
        full_url = '{0}://{1}{2}{3}{4}'.format(
            ssh_tag,
            self.domain,
            self.nginx_uri,
            self.prefix_uri,
            url
        )
        if parames:
            if isinstance(parames, dict):
                parames = urlencode(parames)
            elif isinstance(parames, six.string_types):
                parames = quote(parames, '')
            else:
                parames = parames

            full_url += '?' + parames

        return full_url

    def print_uri(self, print_debug=False):
        """print_uri."""
        try:
            def print_api_key(item):
                assert isinstance(item, (list, tuple))
                if len(item) >= 3 and \
                        isinstance(item[2], dict) and \
                        'api_key' in item[2]:
                    return item[2]['api_key']
                else:
                    return ''

            def is_debug(item):
                assert isinstance(item, (list, tuple))
                if len(item) >= 3 and \
                        isinstance(item[2], dict) and \
                        'rest_option' in item[2]:
                    return item[2]['rest_option'].kwargs.get('is_debug', False)
                else:
                    return False

            str_print = ''
            str_print += '\n*   --------------------------------------------\n'
            str_print += '\n'.join(["*   -- {1:<32} - {0}".format(
                self.make_url(item[0]), print_api_key(item))
                for item in self.http_handler
                if not print_debug or is_debug(item)
            ])
            str_print += '\n*   --------------------------------------------\n'
        except Exception:
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.info(str_print)

    def print_debug_uri(self):
        return self.print_uri(True)

    def print_uri_restful(self):
        """print_uri_restful."""
        try:
            def print_api_key(item):
                assert isinstance(item, (list, tuple))
                if len(item) >= 3 and \
                        isinstance(item[2], dict) and \
                        'api_key' in item[2]:
                    return item[2]['api_key']
                else:
                    return ''

            def print_path_key(item):
                assert isinstance(item, (list, tuple))
                if len(item) >= 3 and \
                        isinstance(item[2], dict) and \
                        'api_key' in item[2]:
                    return item[2]['rest_option'].path
                else:
                    return ''

            str_print = ''
            str_print += '\n*   --------------------------------------------\n'
            str_print += '\n'.join(["*   -- {1:<32} - {0}".format(
                self.make_url(print_path_key(item)),
                print_api_key(item)) for item in self.http_handler])
            str_print += '\n*   --------------------------------------------\n'
        except Exception:
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.info(str_print)


http_app = HttpAppLoader()
