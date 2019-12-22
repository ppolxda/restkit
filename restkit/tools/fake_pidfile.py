import types
import logging
from functools import wraps


class PidFileError(Exception):
    pass


def pidfile(*pid_args, **pid_kwargs):
    if len(pid_args) > 0:
        assert not isinstance(
            pid_args[0], types.FunctionType), "pidfile decorator must be called with parentheses, like: @pidfile()"  # noqa

    def wrapper(func):
        @wraps(func)
        def decorator(*func_args, **func_kwargs):
            return func(*func_args, **func_kwargs)
        return decorator
    return wrapper


class PidFile(object):
    __slots__ = ("pid", "pidname", "piddir", "enforce_dotpid_postfix",
                 "register_term_signal_handler", "register_atexit", "filename",
                 "fh", "lock_pidfile", "chmod", "uid", "gid", "force_tmpdir",
                 "allow_samepid", "_logger", "_is_setup", "_already_removed")

    def __init__(self, pidname=None, piddir=None, enforce_dotpid_postfix=True,
                 register_term_signal_handler='auto', register_atexit=True,
                 lock_pidfile=True, chmod=0o644, uid=-1, gid=-1, force_tmpdir=False,  # noqa
                 allow_samepid=False):
        self.pidname = pidname
        self.piddir = piddir
        self.enforce_dotpid_postfix = enforce_dotpid_postfix
        self.register_term_signal_handler = register_term_signal_handler
        self.register_atexit = register_atexit
        self.lock_pidfile = lock_pidfile
        self.chmod = chmod
        self.uid = uid
        self.gid = gid
        self.force_tmpdir = force_tmpdir
        self.allow_samepid = allow_samepid

        self.fh = None
        self.filename = None
        self.pid = None

        self._logger = None
        self._is_setup = False
        self._already_removed = False

    def check(self):
        pass

    def create(self):
        pass

    def close(self, fh=None, cleanup=None):
        pass

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        self.close()
