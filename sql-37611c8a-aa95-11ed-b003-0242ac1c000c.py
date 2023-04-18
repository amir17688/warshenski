from flask import redirect, make_response
from random import randint

import redis
import uuid
import time


def initRedis_db():
    r = redis.Redis(host='127.0.0.1',port=6379,db=0)
    return r


def generateSession(user_id, r):
    salt = ''.join([chr(randint(97, 122)) for _ in range(32)])
    generate_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(user_id + time.time()) + salt))

    r.set(generate_uuid, user_id)
    response = make_response(redirect('set_cookie'))
    response.set_cookie('SESSION', bytes(generate_uuid, 'utf-8'))