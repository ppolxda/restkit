# -*- coding: utf-8 -*-
"""
@create: 2019-09-28 18:17:55.

@author: name

@desc: report_csv_handler
"""
from restkit.rest import http_app
from restkit.tools.error_info import _
from restkit.tools.field_checker import parames_config
from .report_csv_delete import HttpReportCsvDeleteHandler
from .report_csv_query import HttpReportCsvQueryHandler

# fields = UserAreacodeFeildCheck.fields
# field_keys = UserAreacodeFeildCheck.field_keys
# field_primary_keys = UserAreacodeFeildCheck.field_primary_keys
# field_update_keys = UserAreacodeFeildCheck.field_update_keys

fields = {
    'taskid': {
        "id": 1,
        "dbname": "admins",
        "type": "string",
        "comment": "taskid",
        "options": {
            "update": 'false',
            "maxlen": 32,
            "minlen": 1,
        }
    }
}


@http_app.route()
class HttpUserParamesHandler(HttpReportCsvDeleteHandler,
                             HttpReportCsvQueryHandler):

    requert_parames_config = {
        'report_csv[DELETE]': {
            key: parames_config(fields[key])
            for key in HttpReportCsvDeleteHandler.delete_keys
        },
        'report_csv_download[GET]': {
            key: parames_config(fields[key])
            for key in HttpReportCsvDeleteHandler.delete_keys
        }
    }
