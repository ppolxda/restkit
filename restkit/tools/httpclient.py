# -*- coding: utf-8 -*-
"""
Created on 2016/10/2.

@author: name
"""
from __future__ import absolute_import, division, print_function
import sys
import six
import json
import logging
import datetime
import traceback
import mimetypes
from functools import partial
from tornado import httpclient, gen
from .string_unit import decode_str
# import certifi
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

LOGGER = logging.getLogger(__file__)


# def use_proxy(proxy_host=None, proxy_port=None,
#               proxy_username=None, proxy_password=None):
#     httpclient.AsyncHTTPClient.configure(
#         "tornado.curl_httpclient.CurlAsyncHTTPClient")

#     defaults = dict(ca_certs=certifi.where())
#     defaults['proxy_host'] = proxy_host
#     defaults['proxy_port'] = int(proxy_port)
#     defaults['proxy_username'] = proxy_username
#     defaults['proxy_password'] = proxy_password
#     httpclient.AsyncHTTPClient.configure(
#         "tornado.curl_httpclient.CurlAsyncHTTPClient", defaults=defaults)

if sys.version_info[0] != 3:
    bytes = str


@gen.coroutine
def async_http_request(method, url, body_parames=None, query_parames=None,
                       connect_timeout=None, request_timeout=None,
                       ssl_options=None, headers=None,
                       no_pirnt_req=False, no_pirnt_rsp=False,
                       raise_error=True, isjson=False):
    """async_http_request."""
    http_client = httpclient.AsyncHTTPClient()

    # urlencode
    if isinstance(body_parames, dict):
        if isjson:
            body_parames = json.dumps(body_parames)
        else:
            body_parames = urlencode(body_parames)
    elif isinstance(body_parames, six.string_types) or \
            isinstance(body_parames, six.binary_type):
        body_parames = body_parames
    elif body_parames is None:
        body_parames = body_parames
    else:
        raise TypeError('body_parames type error')

    # urlencode
    if isinstance(query_parames, dict):
        query_parames = urlencode(query_parames)
    elif isinstance(query_parames, six.string_types) or \
            isinstance(query_parames, six.binary_type):
        query_parames = query_parames
    elif query_parames is None:
        query_parames = query_parames
    else:
        raise TypeError('query_parames type error')

    if query_parames:
        url += '?' + query_parames

    response = None
    try:
        start = datetime.datetime.now()
        fetch = http_client.fetch
        response = yield fetch(url, method=method, headers=headers,
                               body=body_parames, ssl_options=ssl_options,
                               connect_timeout=connect_timeout,
                               request_timeout=request_timeout,
                               raise_error=raise_error)

        end = datetime.datetime.now()

        req_data = '' if no_pirnt_req else decode_str(body_parames)
        rsp_data = '' if no_pirnt_rsp else decode_str(response.body)
        LOGGER.debug('httpclient_%s url[%s]\ndata[%s] \nresponse[%s]\n%ss',
                     method, url, req_data, rsp_data, (end - start).seconds)
    except Exception:
        end = datetime.datetime.now()
        req_data = '' if no_pirnt_req else decode_str(body_parames)
        rsp_data = '' if no_pirnt_rsp else decode_str(traceback.format_exc())
        LOGGER.warn('httpclient_%s url[%s]\ndata[%s]\n%s\n%ss', method, url,
                    req_data, rsp_data, (end - start).seconds)

    if not response:
        raise gen.Return(None)
    raise gen.Return(response.body)


async_http_get = partial(async_http_request, 'GET')  # noqa
async_http_post = partial(async_http_request, 'POST')  # noqa
async_http_put = partial(async_http_request, 'PUT')  # noqa
async_http_patch = partial(async_http_request, 'PATCH')  # noqa
async_http_delete = partial(async_http_request, 'DELETE')  # noqa


@gen.coroutine
def async_http_post_file(url, fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    # files = [('image', new_file_name, f.read())]
    # fields = (('api_key', KEY), ('api_secret', SECRET))
    content_type, body = encode_multipart_formdata(fields, files)
    headers = {"Content-Type": content_type, 'content-length': str(len(body))}

    result = yield async_http_post(
        url, body, headers=headers, no_pirnt_req=True)
    raise gen.Return(result)


def encode_multipart_formdata_py2(fields, files, encoding='utf8'):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
    crlf = '\r\n'
    lx = []
    for (key, value) in fields:
        lx.append('--' + boundary)
        lx.append('Content-Disposition: form-data; name="%s"' % key)
        lx.append('')
        lx.append(value)
    for (key, filename, value) in files:
        # filename = encode_utf8(filename)
        lx.append('--' + boundary)
        lx.append(
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                key, filename
            )
        )
        lx.append('Content-Type: %s' % get_content_type(filename))
        lx.append('')
        lx.append(value)
    lx.append('--' + boundary + '--')
    lx.append('')
    body = crlf.join(lx)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body


def encode_multipart_formdata_py3(fields, files, encoding='utf8'):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    boundary = b'----------ThIs_Is_tHe_bouNdaRY_$'
    crlf = b'\r\n'
    lx = []
    for (key, value) in fields:
        if not isinstance(key, bytes):
            key = key.encode(encoding)
        if not isinstance(value, bytes):
            value = value.encode(encoding)

        lx.append(b'--' + boundary)
        lx.append(b'Content-Disposition: form-data; name="%b"' % key)
        lx.append(b'')
        lx.append(value)
    for (key, filename, value) in files:
        if not isinstance(key, bytes):
            key = key.encode(encoding)
        if not isinstance(filename, bytes):
            filename = filename.encode(encoding)
        if not isinstance(value, bytes):
            value = value.encode(encoding)

        # filename = encode_utf8(filename)
        lx.append(b'--' + boundary)
        lx.append(
            b'Content-Disposition: form-data; name="%b"; filename="%b"' % (
                key, filename
            )
        )
        content_type = get_content_type(filename.decode())
        lx.append(b'Content-Type: %b' % content_type.encode(encoding))
        lx.append(b'')
        lx.append(value)
    lx.append(b'--' + boundary + b'--')
    lx.append(b'')
    body = crlf.join(lx)
    content_type = b'multipart/form-data; boundary=%b' % boundary
    return content_type, body


if sys.version_info[0] == 3:
    encode_multipart_formdata = encode_multipart_formdata_py3
else:
    encode_multipart_formdata = encode_multipart_formdata_py2


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# def async(task, *args, **kwargs):
#     future = TracebackFuture()
#     callback = kwargs.pop("callback", None)
#     if callback:
#         IOLoop.instance().add_future(
# future,
#              lambda future: callback(future.result()))
#     result = task(*args, **kwargs)
#     IOLoop.instance().add_callback(_on_result, result, future)
#     return future

# def _on_result(result, future):
#     # if result is not ready, add callback function to next loop,
#     if result:
#         future.set_result(result)
#     else:
#         IOLoop.instance().add_callback(_on_result, result, future)


# if __name__ == "__main__":
#     @gen.coroutine
#     def main():
#         # rsp = yield async_http_post(
# 'http://183.38.71.142:5643/test/url_maker',
#         # {'ordercode': '002', 'sit_no': '1000', 'amount': '1000'})
#         # print(rsp)
#         f = open('./aaa.jpg', 'rb')
#         files = [('files', 'asdasd.jpg', f.read())]
#         fields = (('api_key', 'KEY'), ('api_secret', 'SECRET'))
#         rsp = yield async_http_post_file(
# 'http://192.168.1.24:10200/musers/images/5/upload', fields, files)
#         print(rsp)

#     # import sys
#     # sys.path.append('../')
#     from tornado.ioloop import IOLoop
#     IOLoop.instance().run_sync(main)
