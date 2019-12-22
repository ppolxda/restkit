# -*- coding: utf-8 -*-
"""
@create: 2019-09-28 18:18:54.

@author: name

@desc: report_csv_delete
"""
from tornado import gen
from restkit import rest
from restkit.transactions import trans_func
from restkit.transactions import Transaction
from restkit.handlers.http_mrg_conns.http_sessions import HttpSessionBaseHandler  # noqa
from restkit.tools.error_info import _N
from restkit.tools.error_info import _
from restkit.tools.error_info import error_info

try:
    from report_task.tasks import TaskError
    from report_task.tasks import EnumStatus
except ImportError:
    TaskError = None
    EnumStatus = EnumStatus

# TODO - stoken will be steped


class HttpReportCsvDeleteHandler(HttpSessionBaseHandler):

    delete_keys = ['taskid']

    @rest.delete(api_key='report_csv[DELETE]',
                 path='/report_csv', data_types=[],
                 rest_path=_N('/').join([_('99.Report Csv Manage'),
                                         _('Delete Csv File')]),
                 query_define={})
    def delete_req(self):
        req_data = self.decode_json_from_body()
        req_data = self.filter_whitelist(req_data, self.delete_keys)

        trans = Transaction(
            trans=[
                self.delete_check(req_data) == error_info.ERROR_SUCESS,
                self.delete_processing(req_data) == error_info.ERROR_SUCESS,
            ],
            success=self.delete_sucess,
            failure=self.delete_failure
        )
        yield self.trans_spawn(trans)

    @trans_func
    def delete_check(self, req_data):
        if 'taskid' not in req_data:
            raise gen.Return(self.package_rsp(
                error_info.ERROR_KEY_INVAILD,
                {'key': 'taskid'})
            )

        return error_info.ERROR_SUCESS

    @trans_func
    def delete_processing(self, req_data):
        try:
            task = self.gsettings.csvtask.get_task_by_id(req_data['taskid'])
        except TaskError:
            raise gen.Return(self.package_rsp(
                error_info.ERROR_OP_OBJECT_NOT_FOUND,
                {'desc': 'taskid'})
            )

        taskinfo = task.to_task_dict()
        if taskinfo['userid'] != self.session_userid_str():
            raise gen.Return(self.package_rsp(
                error_info.ERROR_OP_OBJECT_NOT_FOUND,
                {'desc': 'taskid2'})
            )

        task.delete_tasks()
        raise gen.Return(error_info.ERROR_SUCESS)

    @gen.coroutine
    def delete_sucess(self, last_result):
        self.write_error_json(error_info.ERROR_SUCESS)

    @gen.coroutine
    def delete_failure(self, last_result):
        self.write_error_json(last_result)
