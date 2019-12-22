# -*- coding: utf-8 -*-
"""
@create: 2019-09-28 18:09:34.

@author: name

@desc: report_csv_query
"""
import json
from tornado.web import HTTPError
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

# QUERY_DEFINE = areacode_query_sql.QUERY_DEFINE

# TODO - stoken will be steped


class HttpReportCsvQueryHandler(HttpSessionBaseHandler):

    @rest.get(api_key='report_csv[GET]',
              path='/report_csv/list', data_types=[],
              rest_path=_N('/').join([_('99.Report Csv Manage'),
                                      _('Query Csv List')]),
              query_define={})
    def get_req(self, *args, **kwargs):
        trans = Transaction(
            trans=[
                self.get_processing() == error_info.ERROR_SUCESS,
            ]
        )
        yield self.trans_spawn(trans)

    showkey = set(['task_id', 'create_date', 'update_date', 'download_url',
                   'task_status', 'task_text', 'csvname', 'csvdesc'])

    def task_to_json(self, data):
        assert isinstance(data, dict)
        if 'kwargs' in data:
            data.update(data['kwargs'])

        result = {}
        for key, val in data.items():

            if key not in self.showkey:
                continue

            result[key] = val

        if result['task_status'] == EnumStatus.SUCESS:
            result['download_url'] = self.gsettings.make_url(
                '/report_csv/download', {
                    'taskid': result['task_id']
                })
        else:
            result['download_url'] = ''
        return result

    @trans_func
    def get_processing(self):
        result = self.gsettings.csvtask.find_tasks_by_userid(
            self.session_userid_str()
        )
        result = [self.task_to_json(l) for l in result]

        self.write_error_json_raise(
            error_info.ERROR_SUCESS,
            results=result if result is not None else []
        )

    @rest.get(api_key='report_csv_download[GET]',
              path='/report_csv/download', data_types=[],
              rest_path=_N('/').join([_('99.Report Csv Manage'),
                                      _('Downlod Csv File')]),
              query_define={})
    def get_download_req(self, *args, **kwargs):
        # where = self.get_where_parames()
        # req_data = where['where']
        req_data = {
            'taskid': self.get_argument('taskid', None),
            'filename': self.get_argument('filename', None)
        }

        if 'taskid' not in req_data:
            raise HTTPError(404)

        try:
            task = self.gsettings.csvtask.get_task_by_id(req_data['taskid'])
        except TaskError:
            raise HTTPError(405)

        taskinfo = task.to_task_dict()
        if taskinfo['userid'] != self.session_userid_str():
            raise HTTPError(405)

        if task.task_status != EnumStatus.SUCESS:
            raise HTTPError(405)

        if req_data['filename'] is not None:
            csvname = req_data['filename']
        elif 'csvname' in task.kwargs:
            csvname = task.kwargs['csvname']
        else:
            csvname = task.task_id

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header(
            'Content-Disposition',
            b'attachment; filename=%b.csv' % csvname.encode('utf8'))

        filebuf = task.get_csv_file()
        self.write(filebuf)

    def _session_processing(self):
        if not self.need_logged:
            return True

        # query_argument
        sid = self.get_query_argument('sid', None)
        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        # body
        sid = self.get_body_argument('sid', None)
        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        try:
            req_data = self.decode_json_from_body()
        except json.JSONDecodeError:
            req_data = {}
        except UnicodeDecodeError:
            req_data = {}

        # json body
        if isinstance(req_data, dict):
            sid = req_data.get('sid', None)
            if sid is not None and self.session(sid).is_vaild():
                self.session().refresh_sesion()
                return True

        # cookie
        sid = self.get_secure_cookie('sid', None)
        if isinstance(sid, bytes):
            sid = sid.decode()

        if sid is not None and self.session(sid).is_vaild():
            self.session().refresh_sesion()
            return True

        # self.write_error_json(error_info.ERROR_NOT_LOGGED)
        raise HTTPError(401)
