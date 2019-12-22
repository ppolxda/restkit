# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 15:39:58.

@author: name

@desc: transactions
"""
from __future__ import absolute_import, division, print_function
# import inspect
from tornado import gen
# from tornado.ioloop import IOLoop


# def _async_doing(task, *args, **kwargs):
#     future = gen.TracebackFuture()

#     def _on_result(result, future):
#         if result:
#             future.set_result(result)
#         else:
#             IOLoop.instance().add_callback(_on_result, result, future)

#     callback = kwargs.pop("callback", None)
#     if callback:
#         IOLoop.instance().add_future(future,
#                             lambda future: callback(future.result()))
#     result = task(*args, **kwargs)
#     IOLoop.instance().add_callback(_on_result, result, future)
#     return future


def trans_func(func):
    def wrapper(*args, **kwargs):
        return TransCompare(func, *args, **kwargs)
    return wrapper


class Compare(object):

    EQUAL = 'EQUAL'
    NOT_EQUAL = 'NOT_EQUAL'
    LESS = 'LESS'
    GREATER = 'GREATER'
    LESS_EQUAL = 'LESS_EQUAL'
    GREATER_EQUAL = 'GREATER_EQUAL'

    IS_EQUAL = 'IS_EQUAL'
    IS_NOT_EQUAL = 'IS_NOT_EQUAL'


class TransCompare(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.optype = Compare.IS_EQUAL
        self.value = None

        if not callable(func):
            raise TypeError('func can not call')

    # def __call__(self, other):
    #     self.value = other
    #     self.optype = Compare.EQUAL
    #     return self

    def __eq__(self, other):
        self.value = other
        self.optype = Compare.EQUAL
        return self

    def __ne__(self, other):
        self.value = other
        self.optype = Compare.NOT_EQUAL
        return self

    def __lt__(self, other):
        self.value = other
        self.optype = Compare.LESS
        return self

    def __gt__(self, other):
        self.value = other
        self.optype = Compare.GREATER
        return self

    def __le__(self, other):
        self.value = other
        self.optype = Compare.LESS_EQUAL
        return self

    def __ge__(self, other):
        self.value = other
        self.optype = Compare.GREATER_EQUAL
        return self

    def __repr__(self):
        return "{}: {} '{}'".format(self.__class__,
                                    self.optype, self.value)

    def compare(self, val):
        if self.optype == Compare.EQUAL:
            return val == self.value
        elif self.optype == Compare.NOT_EQUAL:
            return val != self.value
        elif self.optype == Compare.LESS:
            return val < self.value
        elif self.optype == Compare.GREATER:
            return val > self.value
        elif self.optype == Compare.LESS_EQUAL:
            return val <= self.value
        elif self.optype == Compare.GREATER_EQUAL:
            return val >= self.value
        elif self.optype == Compare.IS_EQUAL:
            return val is self.value
        elif self.optype == Compare.IS_NOT_EQUAL:
            return val is not self.value
        else:
            raise TypeError('optype invaild')

    @gen.coroutine
    def call_trans(self):
        if not gen.is_coroutine_function(self.func):
            result = yield gen.coroutine(self.func)(*self.args, **self.kwargs)
        else:
            result = yield self.func(*self.args, **self.kwargs)
        raise gen.Return(result)


class Transaction(object):

    def __init__(self, trans=None, success=None, failure=None):
        if trans is None:
            trans = []

        self.trans = trans
        self.success = success
        self.failure = failure
        self.is_invaild_trans()

    def is_invaild_trans(self):
        for trans in self.trans:
            if not isinstance(trans, TransCompare):
                raise TypeError('trans config invaild')

        if self.success is not None and \
                (not callable(self.success) or
                 not gen.is_coroutine_function(self.success)):
            raise TypeError('trans config invaild')

        if self.failure is not None and \
                (not callable(self.failure) or
                 not gen.is_coroutine_function(self.failure)):
            raise TypeError('trans config invaild')

    @gen.coroutine
    def _spawn(self, doing_list):
        result = None
        for trans in doing_list:
            result = yield trans.call_trans()
            if trans.compare(result) is False:
                raise gen.Return((False, result))
        raise gen.Return((True, result))

    @gen.coroutine
    def spawn(self):
        compare, result = yield self._spawn(self.trans)
        if compare is False:
            if self.failure:
                yield self.failure(result)
        else:
            if self.success:
                yield self.success(result)
