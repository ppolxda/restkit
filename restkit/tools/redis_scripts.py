# -*- coding: utf-8 -*-
"""
@create: 2019-08-23 19:01:48.

@author: name

@desc: redis_scripts
"""
import six
from redis import Redis
from redis.exceptions import NoScriptError

INCR_EXPIRE_API_CALL = '''
local current
current = redis.call("incr",KEYS[1])
if tonumber(current) == 1 then
    redis.call("expire", KEYS[1], KEYS[2])
end
return current
'''


class RedisScripts(object):
    """RedisScripts."""

    def __init__(self, *args, **kwargs):
        super(RedisScripts, self).__init__(*args, **kwargs)

        self.__redis_sha = {}

    def __init_sha(self, client, key, script):
        fsha = self.__redis_sha.get(key, None)
        if fsha is None:
            fsha = client.script_load(script)
            self.__redis_sha[key] = fsha
        return fsha

    def incr_expire(self, client, name, ex):
        assert isinstance(name, six.string_types)
        assert isinstance(client, Redis)
        fsha = self.__init_sha(client, 'incr_expire', INCR_EXPIRE_API_CALL)
        try:
            return client.evalsha(fsha, 2, name, ex)
        except NoScriptError:
            self.__redis_sha = {}
            return self.incr_expire(client, name, ex)

    def is_access_limit(self, client, name, ex):
        assert isinstance(name, six.string_types)
        assert isinstance(client, Redis)
        return client.set(name, ex=ex, nx=True) is None
