# -*- coding: utf-8 -*-
"""
@create: 2019-08-26 14:55:19.

@author: name

@desc: mongo mongo_query
"""
import json


BLOCK_QUERY = {
    'email': True,
    'phone': True,
    'idcard': True
}


class QueryParames(Exception):
    pass


class MongoQueryComparisonParse(object):
    """MongoQueryComparisonParse."""

    C_EQ = '$eq'  # ==
    C_GT = '$gt'  # >
    C_GTE = '$gte'  # >=
    C_IN = '$in'  # in
    C_LT = '$lt'  # <
    C_LTE = '$lte'  # <=
    C_NE = '$ne'  # !=
    C_NIN = '$nin'  # not in
    C_LIKE = '$like'  # like
    C_BETWEEN = '$between'  # range
    C_JSON_EQ = '@>'  # pg json

    SQL_EQ = '='
    SQL_GT = '>'
    SQL_GTE = '>='
    SQL_IN = 'IN'
    SQL_LT = '<'
    SQL_LTE = '<='
    SQL_NE = '<>'
    SQL_NIN = 'NOT IN'
    SQL_LIKE = 'LIKE'
    SQL_BETWEEN = 'BETWEEN'
    SQL_JSON_EQ = '@>'

    # can not allow client to use
    C_EXISTS = '$exists'
    C_NEXISTS = '$nexists'
    C_SQL = '$sql'
    SQL_EXISTS = 'EXISTS'
    SQL_NEXISTS = 'NOT EXISTS'
    SQL_SQL = ''

    # regex
    C_REGEX = '$regex'
    SQL_REGEX = 'REGEXP'

    LIMIT_C = [
        C_EXISTS,
        C_NEXISTS,
        C_SQL,
        C_REGEX,
    ]

    C2SQL = {
        C_EQ: SQL_EQ,
        C_GT: SQL_GT,
        C_GTE: SQL_GTE,
        C_IN: SQL_IN,
        C_LT: SQL_LT,
        C_LTE: SQL_LTE,
        C_NE: SQL_NE,
        C_NIN: SQL_NIN,
        C_LIKE: SQL_LIKE,
        C_EXISTS: SQL_EXISTS,
        C_NEXISTS: SQL_NEXISTS,
        C_SQL: SQL_SQL,
        C_REGEX: SQL_REGEX,
        C_BETWEEN: SQL_BETWEEN,
        C_JSON_EQ: SQL_JSON_EQ
    }

    def __init__(self, query_define={}, options_define={}):
        # field defile
        self.query_define = query_define
        # field options
        self.options_define = options_define

    @classmethod
    def pgjson_value(cls, keys, val):
        assert isinstance(keys, list)
        if not keys:
            return val

        key = keys.pop(0)
        return {key: cls.pgjson_value(keys, val)}

    def _parse_sub_str(self, key, op, val, limit):

        if limit and (key not in self.query_define or
                      op in self.LIMIT_C):
            raise QueryParames('query key not define [{}]'.format(key))

        if limit and self.options_define.get(
                key, {}).get('disable_where', BLOCK_QUERY.get(key, False)):
            raise QueryParames('query key not search [{}]'.format(key))

        # Get key in sql
        key = self.query_define.get(key, key)

        if op not in self.C2SQL:
            raise QueryParames('query comparison op error [{}]'.format(op))

        if op in [self.C_IN, self.C_NIN]:

            return '{0} {1} ({2})'.format(
                key, self.C2SQL[op], str('%s, ' * len(val))[:-2]), val

        elif op == self.C_REGEX:
            if isinstance(val, (list, tuple)) and len(val) != 2:
                raise QueryParames(
                    'query format key error [{}][{}][{}]'.format(
                        key, op, val))

            return '{0} %s'.format(self.C2SQL[op]), [val]

        # TAG - SQL BETWEEN
        elif op == self.C_BETWEEN:
            if not isinstance(val, list):
                raise QueryParames(
                    'query comparison val error [{}][{}][{}]'.format(
                        key, op, val))

            return '{0} BETWEEN %s AND %s'.format(key), [val[0], val[1]]

        # TAG - PGJSON
        elif op == self.C_JSON_EQ:
            keys = key.split('.')
            if len(keys) <= 1:
                raise QueryParames(
                    'query format key error [{}][{}][{}]'.format(
                        key, op, val))

            if len(keys) == 3:
                table = keys.pop(0)
                key = keys.pop(0)
                val = json.dumps(self.pgjson_value(keys, val))
                return '{0}.{1} {2} %s'.format(
                    table, key, self.C2SQL[op]), [val]
            else:
                key = keys.pop(0)
                val = json.dumps(self.pgjson_value(keys, val))
                return '{0} {1} %s'.format(key, self.C2SQL[op]), [val]

        elif op in [self.C_EXISTS, self.C_NEXISTS, self.C_SQL]:
            if not isinstance(val, (list, tuple)) and len(val) == 2:
                raise QueryParames(
                    'query comparison val error [{}][{}]'.format(op, val))

            return '{0}({1})'.format(self.C2SQL[op], val[0]), val[1]
        else:
            return '{0} {1} %s'.format(key, self.C2SQL[op]), [val]

    def _parse_sub(self, key, query_dict, limit):
        # { $eq: "ab" }
        assert isinstance(query_dict, dict)

        sqls = []
        vals = []
        for _key, _val in query_dict.items():
            _sqls, _vals = self._parse_sub_str(key, _key, _val, limit)
            sqls.append(_sqls)
            vals += _vals

        if len(sqls) <= 1:
            return ' AND '.join(sqls), vals
        else:
            return '({0})'.format(' AND '.join(sqls)), vals

    def p_parse(self, query, limit):
        assert isinstance(query, dict)

        sqls = []
        vals = []
        for key, val in query.items():
            if not isinstance(val, dict):
                val = {'$eq': val}

            _sqls, _vals = self._parse_sub(key, val, limit)
            sqls.append(_sqls)
            vals += _vals
        return sqls, vals

    def parse(self, query, limit):
        sqls, vals = self.p_parse(query, limit)
        return ' AND '.join(sqls), vals
        # if len(sqls) <= 1:
        #     return ' AND '.join(sqls), vals
        # else:
        #     return '({0})'.format(' AND '.join(sqls)), vals


class MongoQueryParse(object):
    """MongoQueryParse."""

    LOGICAL_AND = '$and'
    # LOGICAL_NOT = '$not'
    # LOGICAL_NOTR = '$nor'
    LOGICAL_OR = '$or'

    SQL_AND = ' AND '
    SQL_OR = ' OR '

    L2SQL = {
        LOGICAL_AND: SQL_AND,
        LOGICAL_OR: SQL_OR,
    }

    def __init__(self, query_define={}, options_define={}):
        """MongoQueryParse."""
        # super(MongoParse, self).__init__(*args)
        # field defile
        self.query_define = query_define
        # field options
        self.options_define = options_define
        # parse
        self.xparse = MongoQueryComparisonParse(
            self.query_define, self.options_define
        )

    def parse(self, query, limit=True):
        assert isinstance(query, dict)

        full_sqls = []
        full_vals = []

        _query = {key: val for key, val in query.items()
                  if key in self.L2SQL and val}

        for key, val in _query.items():
            if not isinstance(val, list):
                raise QueryParames(
                    'query logical val error [{}]'.format(key))

            sqls = []
            vals = []
            for _val in val:
                _sqls, _vals = self.parse(_val, limit)
                sqls.append('({0})'.format(_sqls))
                vals += _vals

            full_sqls += ['({0})'.format(self.L2SQL[key].join(sqls))]
            full_vals += vals

        _query = {key: val for key, val in query.items()
                  if key not in self.L2SQL}

        _sqls, _vals = self.xparse.p_parse(_query, limit)

        full_sqls += _sqls
        full_vals += _vals
        return ' AND '.join(full_sqls), full_vals
