# -*- coding: utf-8 -*-
"""
@create: 2019-09-24 14:32:22.

@author: name

@desc: dbloop
"""
import os
import json
import codecs
import logging
import threading
import traceback
from typing import List
from tornado import gen
from tornado.ioloop import IOLoop
from restkit.database import Database
from restkit.database import DatabaseTrans
# from tools.error_info import _
# from tools.error_info import error_info


class TransError(Exception):
    pass


class HttpDBaseHandler(object):

    __db = {}
    __db_lock = threading.Lock()
    DEFAULT_DBNAME = 'main'

    def __init__(self, **settings):
        # super(PgsqlHandler, self).__init__(*args, **kwargs)
        self.__dbase_trans = None
        self.settings = settings

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

    @gen.coroutine
    def dbase_reset(self):
        try:
            yield self.dbase_rollback()
        except Exception:
            pass

        self.__dbase_trans = None

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

    def get_db_engine(self, name=None):
        if name is None:
            name = self.DEFAULT_DBNAME

        db = self.settings.get('db_engines', {}).get(name, None)
        if db is None:
            raise TypeError('db_engine setting not set')
        return db


class EventLoop(HttpDBaseHandler):

    def __init__(self, name, loop: IOLoop, logger: logging.Logger, **settings):
        super(EventLoop, self).__init__(**settings)
        self.name = name
        self.settings = settings
        self.wloop_name = self.settings.get('wloop_name', None)
        self.wloop_interval = self.settings.get('wloop_interval', 60)
        self.error_interval = self.settings.get('error_interval', 10)
        self.is_start = False
        self.logger = logger
        self.loop = loop

    def start(self):
        self.is_start = True
        self.loop.call_later(1, self.run_loop)

    def stop(self):
        self.is_start = False

    @gen.coroutine
    def run_loop(self, retry=0):
        if not self.is_start:
            return

        loop_interval = self.wloop_interval

        try:
            yield self.run()
        except Exception:
            retry += 1
            loop_interval = self.error_interval
            if self.wloop_name:
                self.logger.warn(
                    '%s [retry:%s][ex:%s]',
                    self.wloop_name, retry,
                    traceback.format_exc()
                )
            else:
                self.logger.warn(
                    '%s [retry:%s][ex:%s]',
                    self.__class__, retry,
                    traceback.format_exc()
                )
        else:
            retry = 0
        finally:
            try:
                yield self.dbase_reset()
            except Exception:
                pass

            self.loop.call_later(
                loop_interval, self.run_loop, retry
            )

    @gen.coroutine
    def run(self):
        raise NotImplementedError


class Task(object):

    def __init__(self, _path: str, _name: str):
        self._path = _path
        self._name = _name
        self.logid = 0

    @property
    def task_file(self):
        return os.path.join(
            self._path, self._name + '.json'
        )

    def load_task(self):
        try:
            with codecs.open(self.task_file, 'r', encoding='utf8') as fs:
                data = json.loads(fs.read())
                self.logid = data['logid']
        except FileExistsError:
            self.logid = 0

    def save_task(self, logid=None):
        if logid:
            self.logid = logid

        with codecs.open(self.task_file, 'w', encoding='utf8') as fs:
            data = json.loads({
                'logid': self.logid,
                'name': self._name
            })
            fs.write(data)


class LogInfo(object):

    def __init__(self, dbtrans, logid, **kwargs):
        self.dbtrans = dbtrans
        self.logid = logid
        self.kwargs = kwargs

    def is_inviald(self):
        raise NotImplementedError

    @gen.coroutine
    def run(self):
        raise NotImplementedError

    @gen.coroutine
    def error(self, text):
        raise NotImplementedError

    @gen.coroutine
    def sucess(self):
        raise NotImplementedError


class LogQuery(object):

    def __init__(self, task: Task):
        self.task = task

    @gen.coroutine
    def get_logs(self, dbtrans) -> List[LogInfo]:
        raise NotImplementedError

    @gen.coroutine
    def commit(self, dbtrans, logs: List[LogInfo]):
        raise NotImplementedError


class LogEventLoop(EventLoop):

    def __init__(self, name, logquery, loop, logger, **settings):
        settings['wloop_name'] = name
        super(LogEventLoop, self).__init__(loop, logger, **settings)
        self.name = name
        self.task = Task(self.settings['task_path'], name)
        self.logquery = logquery(self.task)

    @gen.coroutine
    def run(self):
        while True:
            dbtrans = yield self.dbase_begin(new_trans=True)
            logs = yield self.logquery.get_logs(dbtrans)
            if not logs:
                break

            for loginfo in logs:

                if loginfo.is_inviald():
                    yield loginfo.error('loginfo invaild')
                    continue

                yield loginfo.run()

            yield self.logquery.commit()
