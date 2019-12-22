# -*- coding: utf-8 -*-
"""
@create: 2019-09-28 18:09:50.

@author: name

@desc: query_handler
"""
from restkit.transactions import trans_func
from restkit.handlers.http_user_conns.http_sessions import HttpSessionBaseHandler  # noqa
# from restkit.tools.error_info import _
from restkit.tools.error_info import error_info


class HttpQueryHandler(HttpSessionBaseHandler):

    requert_parames_config = {

    }

    query_sql = None
    query_where_sql = None
    sum_query_sql = None
    sum_query_where_sql = None
    history_query_sql = None
    history_query_where_sql = None
    history_sum_query_sql = None
    history_sum_query_where_sql = None

    QUERY_TODAY_DEFINE = {}
    QUERY_TODAY_SUM_DEFINE = {}
    QUERY_HISTORY_DEFINE = {}
    QUERY_HISTORY_SUM_DEFINE = {}

    # ----------------------------------------------
    #        today query
    # ----------------------------------------------

    def permission_where(self):
        return {
            'userid': self.session().userid
        }

    def conv_result(self, results):
        return results

    @trans_func
    def get_today_processing(self):
        dbtrans = yield self.dbase_begin()

        where = self.get_where_parames()

        permission = self.permission_where()
        if self.query_where_sql:
            permission.update(self.query_where_sql)

        result = yield self.query_sql.query_data(
            dbtrans, where['where'], permission,
            where['page'], where['sort']
        )

        self.write_error_json_raise(
            error_info.ERROR_SUCESS,
            results=self.conv_result(result) if result is not None else []
        )

    @trans_func
    def get_today_sum_processing(self):
        dbtrans = yield self.dbase_begin()

        where = self.get_where_parames()

        permission = self.permission_where()
        if self.sum_query_where_sql:
            permission.update(self.sum_query_where_sql)

        result = yield self.sum_query_sql.query_data(
            dbtrans, where['where'], permission,
            where['page'], where['sort']
        )

        self.write_error_json_raise(
            error_info.ERROR_SUCESS,
            results=self.conv_result(result) if result is not None else []
        )

    @trans_func
    def post_today_csv_processing(self):

        where = self.get_where_parames_from_json()

        permission = self.permission_where()
        if self.query_where_sql:
            permission.update(self.query_where_sql)

        sql_str, sql_parames = self.query_sql.query_sql_string(
            where['where'], permission,
            where['page'], where['sort']
        )

        self.gsettings.csv_add_task(
            self.session_userid_str(),
            sql_str, sql_parames,
            self.QUERY_TODAY_DEFINE['cnname_define'],
            self.QUERY_TODAY_DEFINE['options_define'],
            **where['csv']
        )
        self.write_error_json_raise(error_info.ERROR_SUCESS)

    # ----------------------------------------------
    #        History Query
    # ----------------------------------------------

    @trans_func
    def get_history_processing(self):
        dbtrans = yield self.dbase_begin()

        where = self.get_where_parames()

        permission = self.permission_where()
        if self.history_query_where_sql:
            permission.update(self.history_query_where_sql)

        result = yield self.history_query_sql.query_data(
            dbtrans, where['where'], permission,
            where['page'], where['sort']
        )

        self.write_error_json_raise(
            error_info.ERROR_SUCESS,
            results=self.conv_result(result) if result is not None else []
        )

    @trans_func
    def get_history_sum_processing(self):
        dbtrans = yield self.dbase_begin()

        where = self.get_where_parames()

        permission = self.permission_where()
        if self.history_sum_query_where_sql:
            permission.update(self.history_sum_query_where_sql)

        result = yield self.history_sum_query_sql.query_data(
            dbtrans, where['where'], permission,
            where['page'], where['sort']
        )

        self.write_error_json_raise(
            error_info.ERROR_SUCESS,
            results=self.conv_result(result) if result is not None else []
        )

    @trans_func
    def post_history_csv_processing(self):

        where = self.get_where_parames_from_json()

        permission = self.permission_where()
        if self.history_query_where_sql:
            permission.update(self.history_query_where_sql)

        sql_str, sql_parames = self.history_query_sql.query_sql_string(
            where['where'], permission,
            where['page'], where['sort']
        )

        self.gsettings.csv_add_task(
            self.session_userid_str(),
            sql_str, sql_parames,
            self.QUERY_TODAY_DEFINE['cnname_define'],
            self.QUERY_TODAY_DEFINE['options_define'],
            **where['csv']
        )
        self.write_error_json_raise(error_info.ERROR_SUCESS)
