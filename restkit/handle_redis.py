# -*- coding: utf-8 -*-
"""
@create: 2019-10-15 17:40:40.

@author: name

@desc: handle_redis
"""
import copy
import redis
import threading
from tornado import web


class RedisHandler(web.RequestHandler):

    # __redis_pools = {}
    # __redis_pools_lock = threading.Lock()

    DEFAULT_REDIS_NAME = 'redis_url'

    def __init__(self, *args, **kwargs):
        super(RedisHandler, self).__init__(*args, **kwargs)
        self.__redis_trans = None

    def redis_client(self, name=None):
        return self.get_redis_cli(name)

    def redis_begin(self, name=None, new_trans=False):
        if new_trans or self.__redis_trans is None:
            redis_client = self.get_redis_cli(name)
            assert isinstance(redis_client, redis.Redis)
            self.__redis_trans = redis_client.pipeline()
        return self.__redis_trans

    def redis_commit(self):
        if self.__redis_trans is None:
            raise AttributeError('redis_trans undefine')

        result = self.__redis_trans.execute()
        self.__redis_trans = None
        return result

    def redis_rollback(self):
        if self.__redis_trans is None:
            raise AttributeError('redis_trans undefine')

        self.__redis_trans.reset()
        self.__redis_trans = None

    def get_redis_cli(self, name=None) -> redis.Redis:
        if name is None:
            name = self.DEFAULT_REDIS_NAME

        db = self.settings.get('db_engines', {}).get(name, None)
        if db is None:
            raise TypeError('db_engine settings not set')
        if not isinstance(db, redis.Redis):
            raise TypeError('db_engine settings invaild')
        return db

    # @property
    # def _redis_config(self):
    #     if self.settings.get('driver', None) == 'redis' and \
    #             'driver_config' in self.settings:
    #         redis_config = self.settings['driver_config']
    #     elif 'redis_config' in self.settings:
    #         redis_config = self.settings['redis_config']
    #     else:
    #         raise AttributeError('redis_config not set')

    #     return redis_config

    # def __init__redis_config(self, db=0):
    #     if db not in RedisHandler.__redis_pools:
    #         with RedisHandler.__redis_pools_lock:
    #             if db not in RedisHandler.__redis_pools:
    #                 redis_config = copy.deepcopy(self._redis_config)
    #                 redis_config['db'] = db

    #                 if 'url' in redis_config:
    #                     client = redis.from_url(**redis_config)
    #                 else:
    #                     client = redis.Redis(**redis_config)

    #                 self.redis_init(client)
    #                 RedisHandler.__redis_pools[db] = client

    #     return RedisHandler.__redis_pools[db]
