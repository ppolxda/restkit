# -*- coding: utf-8 -*-
"""
@create: 2019-08-26 16:09:26.

@author: name

@desc: apikey_api
"""
import json
from tornado import gen


MENU_APIKEY = 'menu_apikey'
SUCESS_APIKEYS = ['menu/folder']


def get_muser_role_by_userid(redis_cli, userid):
    key = 'muser_role:userid:{}'.format(userid)
    return redis_cli.smembers(key)


def is_has_key_by_userid(redis_cli, userid):
    key = 'muser_menu:userid:{}'.format(userid)
    return redis_cli.exists(key)


def is_has_apikey_by_userid(redis_cli, userid, apikey):
    if apikey in SUCESS_APIKEYS:
        return 1

    menuids = redis_cli.hget(MENU_APIKEY, apikey)
    if not menuids:
        return 0

    menuids = json.loads(menuids)
    for menuid in menuids:
        key = 'muser_menu:userid:{}'.format(userid)
        if redis_cli.sismember(key, menuid):
            return 1
    return 0


def is_has_apikey_by_roleid(redis_cli, roleid, apikey):
    if apikey in SUCESS_APIKEYS:
        return 1

    menuids = redis_cli.hget(MENU_APIKEY, apikey)
    if not menuids:
        return 0

    menuids = json.loads(menuids)
    for menuid in menuids:
        key = 'muser_menu:roleid:{}'.format(roleid)
        if redis_cli.sismember(key, menuid):
            return 1
    return 0
