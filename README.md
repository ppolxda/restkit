# restkit

## install

```bash
 pip3 install git+https://github.com/ppolxda/restkit
```


### restful main example

```python
# -*- coding: utf-8 -*-
"""
Created on 2019-08-23 17:25:06.

@author: name
"""
import redis
import signal
import logging
import traceback
from tornado import log
from tornado import ioloop
from sqlalchemy import create_engine
from restkit import http_app
from restkit import collect_local_modules
# from version import version
from .config import Settings

collect_local_modules(
    '.oauth_service.oauth_mrgs_service.http_handlers'
)
from .http_handlers import collect_modules  # noqa
from restkit.handlers.http_mrg_handlers import collect_modules  # noqa


PNAME = 'oauth_mrgs_service'
LOGGER = logging.getLogger(PNAME)
log.access_log = logging.getLogger('oauth_mrgs_service')
settings = Settings(PNAME)


def config_settings():
    return {
        'session_secret': settings.session_secret,
        'cookie_secret': settings.cookie_secret,
        'session_expire': settings.login_sid_timeout,
        'session_key_fmt':  settings.session_key_fmt,
        'session_index_fmt': settings.session_index_fmt,
        'gsettings': settings,
        'logger': LOGGER,

        'jwt_iss': settings.jwt_iss,
        'jwt_mode': settings.jwt_mode,
        'jwt_secret': settings.jwt_secret,
        'jwt_priv_path': settings.jwt_priv_path,
        'jwt_priv_pwd': settings.jwt_priv_pwd,
        'jwt_pub_path': settings.jwt_pub_path,

        'db_engines': {
            'main': create_engine(
                settings.pgsql_url,
                pool_size=settings.pgsql_pool_size,
                pool_pre_ping=True
            ),
            'slave': create_engine(
                settings.pgsql_slaves_url,
                pool_size=settings.pgsql_pool_size,
                pool_pre_ping=True
            ),
            'redis_url': redis.from_url(
                settings.redis_url, decode_responses=True
            ),
            'session_db': redis.from_url(
                settings.redis_url, decode_responses=True
            ),
            'muser_db': redis.from_url(
                settings.muser_url, decode_responses=True
            ),
            'auth_db': redis.from_url(
                settings.auth_url, decode_responses=True
            )
        },
        'ssl_options': settings.ssl_options
    }


def main():
    LOGGER.info(settings.print_config())

    # init_db()
    io_loop = ioloop.IOLoop.current()
    http_app.set_domain(settings.domain)
    http_app.set_nginx_uri(settings.nginx_uri)
    http_app.set_use_ssh_tag(settings.use_ssh)
    http_app.set_logger_name(PNAME)
    # http_app.set_prefix_uri(settings.prefix_uri)
    # http_app.set_domain('192.168.1.126:9999')
    # http_app.set_nginx_uri('/api')
    # http_app.set_use_ssh_tag(settings.use_ssh)
    # http_app.set_prefix_uri(settings.prefix_uri)
    # http_app.set_domain('192.168.1.24:10000')

    DEFAULT_SETTIONGS = config_settings()
    http_app.listen(settings.listen_port, **DEFAULT_SETTIONGS)
    http_app.print_uri()
    http_app.print_debug_uri()
    try:
        def on_shutdown():
            """on_shutdown."""
            LOGGER.info('shutdown service')
            io_loop.stop()

        signal.signal(signal.SIGINT, lambda sig,
                      frame: io_loop.add_callback_from_signal(on_shutdown))
        io_loop.start()
    except KeyboardInterrupt:
        on_shutdown()
    except Exception:  # noqa
        LOGGER.info(traceback.format_exc())

    LOGGER.info('services had exit')


if __name__ == "__main__":
    main()
```

### restful handler example

```python
# -*- coding: utf-8 -*-
"""
@create: 201p-10-26 14:13:49.

@author: name

@desc: sys_role_insert
"""
from tornado import gen
from restkit import rest
from restkit import trans_func
from restkit import Transaction
from oauth_service.oauth_mrgs_service.handlers import HttpBaseHandler
from oauth_service.tools.sql.tables.admins_sql import SysRole
from oauth_service.tools.sql.tables.admins_fields import SysRoleFeildCheck
from oauth_service.tools.error_info import _, _N
from oauth_service.tools.error_info import error_info


class HttpSysRoleInesertHandler(HttpBaseHandler):

    @rest.post(api_key='sys_role[POST]',
               path='/sys/roles', data_types=[],
               rest_path=_N('/').join([_('3.System Settings'),
                                       _('Syetem Role Settings'),
                                       _('Create User Role')]))
    def insert_req(self):

        req_data = self.decode_json_from_body()

        trans = Transaction(
            trans=[
                self.insert_check(req_data) == error_info.ERROR_SUCESS,
                self.insert_processing(req_data) == error_info.ERROR_SUCESS,
            ],
            success=self.insert_sucess,
            failure=self.insert_failure
        )
        yield self.trans_spawn(trans)

    @trans_func
    def insert_check(self, req_data):
        SysRoleFeildCheck.fields_insert_check(req_data, ['roleid'])
        return error_info.ERROR_SUCESS

    @trans_func
    def insert_processing(self, req_data):
        dbtrans = yield self.dbase_begin()

        result = yield dbtrans.insert(SysRole, **req_data)
        if result is None:
            raise gen.Return(self.package_rsp(
                error_info.ERROR_DB_ERROR, {'table': 'sysrole'}))

        req_data['roleid'] = result.lastrowid
        raise gen.Return(error_info.ERROR_SUCESS)

    @gen.coroutine
    def insert_sucess(self, last_result):
        yield self.dbase_commit()
        self.write_error_json(error_info.ERROR_SUCESS)

    @gen.coroutine
    def insert_failure(self, last_result):
        self.write_error_json(last_result)

```
