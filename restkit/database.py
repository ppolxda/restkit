# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 15:22:10.

@author: name

@desc: database
"""
# from tornado import gen
# from peewee import SQL
# from peewee import BaseModel
# from tornado_mysql import pools, cursors
import os
import sys
from tornado import gen
from inspect import isclass
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy import insert, update, delete
from sqlalchemy.engine import Engine
from sqlalchemy.engine import Connection
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.dialects import mysql

try:
    from functools import reduce
except ImportError:
    pass

Base = declarative_base()
PRINT_SQL = os.environ.get('PRINT_SQL', None)


class PgsqlResult(object):

    def __init__(self, conn: Connection, rowcount):
        # self.lastrowid = lastrowid
        self.rowcount = rowcount
        self.conn = conn

    @property
    def lastrowid(self):
        return self._get_lastid()

    def _get_lastid(self):
        _result = self.conn.execute('SELECT LASTVAL() AS lastval;')
        result = _result.fetchone()
        if isinstance(result, tuple):
            result = result[0]
        else:
            result = result['lastval']
        return result


class ModelBase(object):

    primary_cache = {}
    columns_cache = {}

    @classmethod
    def model_clone(cls, model):
        columns = cls._model_columns(model)
        newobject = model.__class__()
        for key in columns:
            newobject.__dict__[key] = model.__dict__.get(key, None)
            # setattr(newobject, key, getattr(model, key))
        return newobject

    @classmethod
    def _model_class(cls, val):
        if not isclass(val):
            assert cls._is_sa_mapped(val.__class__)
            return val.__class__
        else:
            return val

    @classmethod
    def _model_primary(cls, val):
        clsmod = cls._model_class(val)
        columns = inspect(clsmod).primary_key
        return [key.name.lower() for key in columns]

        # cache_key = '__tab_{}_primarys'.format(val.__class__.__name__)
        # if cache_key not in cls.primary_cache:
        #     clsmod = cls._model_class(val)
        #     columns = inspect(clsmod).primary_key
        #     cls.primary_cache.update(
        #         {cache_key: [key.name.lower() for key in columns]})
        # return cls.primary_cache.get(cache_key)

    @classmethod
    def _model_columns(cls, val):
        clsmod = cls._model_class(val)
        columns = inspect(clsmod).columns
        return {key.name.lower(): key for key in columns}

        # cache_key = '__tab_{}_columns'.format(val.__class__.__name__)
        # if cache_key not in cls.columns_cache:
        #     clsmod = cls._model_class(val)
        #     columns = inspect(clsmod).columns
        #     cls.columns_cache.update(
        #         {cache_key: {key.name.lower(): key for key in columns}})
        # return cls.columns_cache.get(cache_key)

    @classmethod
    def _model_to_dict(cls, val):
        columns = cls._model_columns(val)
        return {key: val.__dict__[key]
                for key in val.__dict__
                if key in columns and val.__dict__[key] is not None}

    @classmethod
    def _is_sa_mapped(cls, val):
        try:
            class_mapper(val)
            return True
        except Exception:  # noqa
            return False


class DatabaseSql(ModelBase):
    """DatabaseSql."""

    # ----------------------------------------------
    #        execute_sql
    # ----------------------------------------------

    def execute_sql(self, query, args=None):
        raise NotImplementedError

    # ----------------------------------------------
    #        debug print format sql
    # ----------------------------------------------

    @staticmethod
    def pring_fmt_sql(sql_str, sql_parames):
        try:
            print(sql_str.replace('%%', '%').replace(
                '%s', '\'%s\'') % tuple(sql_parames))
        except Exception:
            pass
        else:
            return

        try:
            print(sql_str.replace('%s', '\'%s\'') % tuple(sql_parames))
        except Exception:
            pass
        else:
            return

        try:
            print(sql_str % tuple(sql_parames))
        except Exception:
            pass
        else:
            return

        try:
            print(sql_str, sql_parames)
        except Exception:
            pass
        else:
            return

    # ----------------------------------------------
    #        sql Conver
    # ----------------------------------------------

    @classmethod
    def insert_sql(cls, model, **args):
        """insert_sql."""
        if isclass(model):
            assert cls._is_sa_mapped(model)
            model_dict = args
            model_class = model
        else:
            assert cls._is_sa_mapped(model.__class__)
            model_dict = cls._model_to_dict(model)
            model_class = model.__class__

        insert_obj = insert(model_class).values(**model_dict)
        insert_obj = insert_obj.compile(dialect=mysql.dialect(),
                                        compile_kwargs={
                                            "literal_binds": False})

        sql_str = str(insert_obj)
        sql_parames = [insert_obj.params[key]
                       for key in insert_obj.positiontup]

        if PRINT_SQL:
            cls.pring_fmt_sql(sql_str, sql_parames)

        return sql_str, sql_parames

    @classmethod
    def insert_many_sql(cls, model, rows, validate_fields=True):
        """insert_many_sql."""
        if not isclass(model) or not cls._is_sa_mapped(model):
            raise TypeError('model must is class')

        if isclass(model):
            assert cls._is_sa_mapped(model)
            model_class = model
        else:
            raise TypeError('model invaild')

        if not rows:
            raise TypeError('rows invaild')

        insert_obj = insert(model_class).values(**rows[0])
        insert_obj = insert_obj.compile(dialect=mysql.dialect(),
                                        compile_kwargs={
                                            "literal_binds": False})

        sql_str = str(insert_obj)
        sql_parames = [
            [row[key] for key in insert_obj.positiontup]
            for row in rows
        ]

        # if PRINT_SQL:
        #     cls.pring_fmt_sql(sql_str, sql_parames)
        return sql_str, sql_parames

    @classmethod
    def insert_many_sql2(cls, model, rows, validate_fields=True):
        """insert_many_sql2."""
        if not isclass(model) or not cls._is_sa_mapped(model):
            raise TypeError('model must is class')

        _rows = []
        for row in rows:
            if isinstance(row, dict):
                model_dict = row
                model_class = model
            elif isinstance(row, object) and cls._is_sa_mapped(row.__class__):
                model_dict = cls._model_to_dict(row)
                model_class = row.__class__
            else:
                raise TypeError('rows list model error')

            if model_class != model:
                raise TypeError('rows model not same')

            _rows.append(model_dict)

        insert_obj = insert(model).values(_rows)
        insert_obj = insert_obj.compile(dialect=mysql.dialect(),
                                        compile_kwargs={
                                            "literal_binds": False})

        sql_str = str(insert_obj)
        sql_parames = [insert_obj.params[key]
                       for key in insert_obj.positiontup]

        # if PRINT_SQL:
        #     cls.pring_fmt_sql(sql_str, sql_parames)
        return sql_str, sql_parames

    @classmethod
    def update_sql(cls, model, allow_update, **args):
        """update_sql."""
        assert allow_update is None or isinstance(allow_update, (list, set))
        if isclass(model):
            assert cls._is_sa_mapped(model)
            model_dict = args
            model_class = model
        else:
            assert cls._is_sa_mapped(model.__class__)
            model_dict = cls._model_to_dict(model)
            model_class = model.__class__

        try:
            where = model_dict.pop('where')
        except KeyError:
            where = None

        primary_keys = cls._model_primary(model_class)

        if allow_update is None:
            update_keys = {i: model_dict[i] for i in model_dict
                           if i not in primary_keys}
        else:
            update_keys = {i: model_dict[i] for i in model_dict
                           if i not in primary_keys and i in allow_update}

        if not update_keys:
            raise KeyError('update_keys null[{}][allow_update:{}]'.format(
                update_keys, allow_update))

        columns = cls._model_columns(model_class)
        update_obj = update(model_class)

        if where:
            where_keys = [columns[i] == where[i]
                          for i in where if i in columns]
        else:
            if set(primary_keys) != set(key for key in model_dict
                                        if key in primary_keys):
                raise KeyError('primary_keys not enough')

            where_keys = [columns[i] == model_dict[i]
                          for i in primary_keys if i in primary_keys]

        update_obj = reduce(lambda x, y: x.where(y),
                            where_keys, update_obj)

        if 'updatetime' in columns:
            update_keys['updatetime'] = text('Now()')

        update_obj = update_obj.values(**update_keys)
        update_obj = update_obj.compile(dialect=mysql.dialect(),
                                        compile_kwargs={
                                            "literal_binds": False})

        sql_str = str(update_obj)
        sql_parames = [update_obj.params[key]
                       for key in update_obj.positiontup]

        if PRINT_SQL:
            cls.pring_fmt_sql(sql_str, sql_parames)

        return sql_str, sql_parames

    @classmethod
    def delete_sql(cls, model, **args):
        """delete_sql."""
        if isclass(model):
            assert cls._is_sa_mapped(model)
            model_dict = args
            model_class = model
        else:
            assert cls._is_sa_mapped(model.__class__)
            model_dict = cls._model_to_dict(model)
            model_class = model.__class__

        try:
            where = model_dict.pop('where')
        except KeyError:
            where = None

        columns = cls._model_columns(model_class)
        delete_obj = delete(model_class)

        if where:
            where_keys = [columns[i] == where[i]
                          for i in where if i in columns]
        else:
            primary_keys = cls._model_primary(model_class)

            if set(primary_keys) != set(key for key in model_dict
                                        if key in primary_keys):
                raise KeyError('primary_keys not enough')

            where_keys = [columns[i] == model_dict[i]
                          for i in primary_keys if i in primary_keys]

        delete_obj = reduce(lambda x, y: x.where(y),
                            where_keys, delete_obj)
        delete_obj = delete_obj.compile(dialect=mysql.dialect(),
                                        compile_kwargs={
                                            "literal_binds": False})

        sql_str = str(delete_obj)
        sql_parames = [delete_obj.params[key]
                       for key in delete_obj.positiontup]

        if PRINT_SQL:
            cls.pring_fmt_sql(sql_str, sql_parames)

        return sql_str, sql_parames


class DatabaseTrans(DatabaseSql):

    def __init__(self, conn: Connection, **settings):
        self.conn = conn
        self.settings = settings
        if self.conn:
            self.driver = self.conn.engine.driver
            self.trans = self.conn.begin()
        else:
            self.driver = None
            self.trans = None

    @gen.coroutine
    def insert(self, model, **args):
        query = self.insert_sql(model, **args)
        result = self.conn.execute(query[0], query[1])

        # lastrowid
        rowcount = result.rowcount
        if rowcount > 0:
            if self.driver == 'psycopg2':
                raise gen.Return(PgsqlResult(self.conn, rowcount))
            else:
                raise gen.Return(result)
        else:
            raise gen.Return(None)

    @gen.coroutine
    def insert_many(self, model, rows, validate_fields=True):
        query = self.insert_many_sql(model, rows, validate_fields)
        result = self.conn.execute(query[0], query[1])

        if result.rowcount > 0:
            raise gen.Return(result)
        else:
            raise gen.Return(None)

    @gen.coroutine
    def update(self, model, allow_update, **kwargs):
        query = self.update_sql(model, allow_update, **kwargs)
        result = self.conn.execute(query[0], query[1])

        if result.rowcount > 0:
            raise gen.Return(result)
        else:
            raise gen.Return(None)

    @gen.coroutine
    def delete(self, model, **args):
        # query = self.delete_sql(model, **args)
        query = self.delete_sql(model, **args)
        result = self.conn.execute(query[0], query[1])

        if result.rowcount > 0:
            raise gen.Return(result)
        else:
            raise gen.Return(None)

    @gen.coroutine
    def execute_sql(self, statement, *multiparams, **params):
        result = self.conn.execute(
            statement, *multiparams, **params
        )
        raise gen.Return(result)

    @gen.coroutine
    def executemany_sql(self, statement, *multiparams, **params):
        result = self.conn.execute(
            statement, *multiparams, **params
        )
        raise gen.Return(result)

    @gen.coroutine
    def begin(self):
        result = self.trans.begin()
        raise gen.Return(result)

    @gen.coroutine
    def commit(self):
        result = self.trans.commit()
        try:
            self.conn.close()
        except Exception as ex:
            pass
        raise gen.Return(result)

    @gen.coroutine
    def rollback(self):
        result = self.trans.rollback()
        try:
            self.conn.close()
        except Exception as ex:
            pass
        raise gen.Return(result)

    @gen.coroutine
    def dbase_commit(self):
        result = self.commit()
        raise gen.Return(result)

    @gen.coroutine
    def dbase_rollback(self):
        result = yield self.rollback()
        raise gen.Return(result)


class Database(object):
    """Database."""

    trans_cls = DatabaseTrans

    def __init__(self, engine: Engine, **settings):
        self.engine = engine
        self.settings = settings

    # ----------------------------------------------
    #        get conncet
    # ----------------------------------------------

    def connect(self):
        return DatabaseTrans(
            self.engine.connect(), **self.settings
        )

    def execute_sql(self, statement, *multiparams, **params):
        return self.engine.execute(statement, *multiparams, **params)

    def begin(self):
        return self.engine.begin()
