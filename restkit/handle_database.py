# -*- coding: utf-8 -*-
"""
Created on 2019-10-15 15:50:38.

@author: name
"""
from __future__ import absolute_import, division, print_function
import logging
import threading
from tornado import gen
from tornado import web
from sqlalchemy.engine import Engine
from sqlalchemy.engine import ResultProxy
from sqlalchemy.engine import RowProxy
# from tornado import httputil
from restkit.tools.string_unit import decode_str
from restkit.database import Database
from restkit.database import DatabaseTrans

try:
    from urllib.parse import urlencode, unquote
except ImportError:
    from urllib import urlencode, unquote


LOGGER_LOG = logging.getLogger('restkit')


class XRowProxy(RowProxy):

    def get(self, key, defval=None):
        if not self.has_key(key):
            return defval
        return self[key]


ResultProxy._process_row = XRowProxy


class HttpDBaseHandler(web.RequestHandler):

    __db = {}
    __db_lock = threading.Lock()
    DEFAULT_DBNAME = 'main'

    def __init__(self, *args, **kwargs):
        super(HttpDBaseHandler, self).__init__(*args, **kwargs)
        self.__dbase_trans = None

    @gen.coroutine
    def dbase_execute(self, name, statement, *multiparams, **params):
        engine = self.dbase_engine(name)
        result = engine.execute_sql(statement, *multiparams, **params)
        raise gen.Return(result)

    @gen.coroutine
    def dbase_trans(self, name=None) -> DatabaseTrans:
        dbase = self.dbase_engine(name)
        conn = dbase.connect()
        raise gen.Return(conn)

    @gen.coroutine
    def dbase_begin(self, name=None) -> DatabaseTrans:
        if self.__dbase_trans is None:
            self.__dbase_trans = yield self.dbase_trans(name)
        raise gen.Return(self.__dbase_trans)

    @gen.coroutine
    def dbase_commit(self):
        if self.__dbase_trans is None:
            raise AttributeError('dbase_trans undefine')

        result = yield self.__dbase_trans.commit()
        raise gen.Return(result)

    @gen.coroutine
    def dbase_rollback(self):
        if self.__dbase_trans is None:
            raise AttributeError('dbase_trans undefine')

        result = yield self.__dbase_trans.rollback()
        raise gen.Return(result)

    def dbase_engine(self, name=None) -> Database:
        if name is None:
            name = self.DEFAULT_DBNAME

        if name not in HttpDBaseHandler.__db:
            with HttpDBaseHandler.__db_lock:
                if name not in HttpDBaseHandler.__db:
                    HttpDBaseHandler.__db[name] = Database(
                        self.get_db_engine(name),
                        **self.settings
                    )

        return HttpDBaseHandler.__db[name]

    def get_db_engine(self, name=None) -> Engine:
        if name is None:
            name = self.DEFAULT_DBNAME

        db = self.settings.get('db_engines', {}).get(name, None)
        if db is None:
            raise TypeError('db_engine setting not set')
        return db
