# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 13:03:50.

@author: name

@desc: http_sessions_handle
"""
from __future__ import absolute_import, division, print_function
import threading
from tornado import web
from .http_sessions import Session
from .http_sessions import SessionSettings


class InvalidSessionException(Exception):
    pass


class HttpSessionHandler(web.RequestHandler):

    __session_settings_lock = threading.Lock()
    __session_settings = None

    def __init__(self, *args, **kwargs):
        super(HttpSessionHandler, self).__init__(*args, **kwargs)
        session_settings = self.session_config()
        self._session_obj = Session(session_settings)

    def session(self, session_id=None) -> Session:
        session_settings = self.session_config()

        if session_id is not None:
            self._session_obj = Session(session_settings, session_id)
            self._session_obj.reload_sesion()

        return self._session_obj

    def session_config(self):
        if HttpSessionHandler.__session_settings is None:
            with HttpSessionHandler.__session_settings_lock:
                if HttpSessionHandler.__session_settings is None:
                    HttpSessionHandler.__session_settings = SessionSettings(
                        **self.settings
                    )
        return HttpSessionHandler.__session_settings
