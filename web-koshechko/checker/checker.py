#!/usr/bin/env python3

import sys
import json
import traceback
import aiohttp, json
import bs4
import requests
import re
import api
import time, datetime
import random
import asyncio
import generators
import redis

from uuid import UUID, uuid4
from typing import List
from aiohttp import client_exceptions, web_exceptions, http_exceptions
from gornilo import (
    CheckRequest,
    Verdict,
    PutRequest,
    GetRequest,
    NewChecker,
    VulnChecker,
)

from generators import (
    random_string,
    random_string_in_range
)

from models import *

checker = NewChecker()

DOWN_EXCEPTIONS = {
    client_exceptions.ServerConnectionError,
    client_exceptions.ClientConnectorError,
    client_exceptions.ServerTimeoutError,
    client_exceptions.ServerDisconnectedError,
    client_exceptions.ClientOSError,
}
MUMBLE_EXCEPTIONS = {
    http_exceptions.HttpProcessingError,
    client_exceptions.ClientResponseError,
    client_exceptions.ContentTypeError,
    client_exceptions.TooManyRedirects,
    json.decoder.JSONDecodeError,
    web_exceptions.HTTPClientError,
    http_exceptions.BadHttpMessage,
    api.ErrorCode,
}
KNOWN_EXCEPTIONS = DOWN_EXCEPTIONS | MUMBLE_EXCEPTIONS


# disable if you don't want to use redis. This disables one of the exploits
DISABLE_DELETION = False

red = redis.Redis(
    host='10.150.0.21',
    # password='____',
    port=26379,
    decode_responses=True
)

DELETED = "DELETED"

def get_deleted(x: str) -> bool:
    if DISABLE_DELETION:
        return False

    try:
        res = red.get(x)
        if res is not None:
            return True
    except Exception:
        return None

def set_deleted(x: str):
    if DISABLE_DELETION:
        return
    res = red.set(x, "yes")


class ErrorChecker:
    def __init__(self):
        self.verdict = Verdict.OK()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type and any(
            issubclass(exc_type, exception) for exception in DOWN_EXCEPTIONS
        ):
            self.verdict = Verdict.DOWN("Service is down")

        elif exc_type and any(
            issubclass(exc_type, exception) for exception in MUMBLE_EXCEPTIONS
        ):
            self.verdict = Verdict.MUMBLE("Service is mumbled")

        elif exc_type == Verdict:
            self.verdict = exc_value

        if exc_type:
            traceback.print_tb(exc_traceback, file=sys.stdout)
            if exc_type not in KNOWN_EXCEPTIONS:
                raise exc_value

        return True


async def eventually(
    f,
    check,
    *args
):
    t0 = time.monotonic()
    DELAY = 0.35 # 350ms
    MAX_TIME = 5 # 5s
    res = None

    while True:
        if time.monotonic() - t0 > MAX_TIME:
            break
        res = await f(*args)
        time.sleep(DELAY)
        if check(res):
            break
    
    return res

import logging


@checker.define_check
async def check_service(request: CheckRequest) -> Verdict:
    logging.basicConfig()
    logging.getLogger().setLevel(logging.ERROR)

    with ErrorChecker() as ec:
        client = api.KoshechkoClient(request.hostname, api.SERVICE_PORT)
        async with aiohttp.ClientSession() as session:
            async with aiohttp.ClientSession() as session2:
                kosh = await check(session, session2, client)
            
            ec.verdict = Verdict.OK()

    return ec.verdict


async def check(session, session2, client) -> Koshechko:
    login = generators.random_login()
    password = generators.random_string_in_range(20, 40)
    cat_name = generators.random_cat()
    public_info = generators.random_desc()
    test_flag = generators.random_string_in_range(20, 40)

    top_cat = await client.top_koshechko(session)
    top_users = await client.top_users(session)

    await client.register(session, login, password)

    token = await client.login(session, login, password)

    session.headers.update({"token": token})            

    await client.kosh_create(session, cat_name, test_flag, [login])

    res = await eventually(
        client.kosh_view,
        lambda x: x.rank != 0 and x.score != 0,
        session, cat_name
    )

    if (
        res.name != cat_name or
        res.owner != login or
        res.score != 1 or
        res.text != test_flag or
        res.shared_with != [login]
    ):
        raise Verdict.MUMBLE("freshly created koshecko is broken")

    top_cat = await client.top_koshechko(session)
    if not any([x.name == cat_name for x in top_cat]):
        raise Verdict.MUMBLE("freshly created koshechko is not present in the top")

    user_present = lambda top: any([x.name == login for x in top])
    get_score = lambda top: any([x.name == login for x in top])
    top_users = await client.top_users(session)

    if not user_present(top_users):
        raise Verdict.MUMBLE("new user is not present in the scoreboard")

    # add new user, share also to him, login as him and check that sharing works

    login2 = generators.random_login()
    password2 = generators.random_string_in_range(20, 40)
    await client.register(session2, login2, password2)
    token2 = await client.login(session2, login2, password2)
    session2.headers.update({"token": token2})            

    users_to_share = [x.name for x in random.choices(top_users, k=random.randint(1, 4))]
    users_to_share.append(login2)
    users_to_share = list(set(users_to_share))

    cat_name = generators.random_cat()
    test_flag = generators.random_string_in_range(20, 40)
    await client.kosh_create(session, cat_name, test_flag, users_to_share)

    res = await eventually(
        client.kosh_view,
        lambda x: x.rank != 0 and x.score != 0,
        session, cat_name
    )
    if (
        res.name != cat_name or
        res.owner != login or
        res.text != test_flag or
        res.shared_with != users_to_share
    ):
        raise Verdict.MUMBLE("freshly created koshecko is broken")
    
    res2 = await client.kosh_view(session2, cat_name)
    if (
        res.name != cat_name or
        res.owner != login or
        res.text != test_flag or
        res.shared_with != users_to_share
    ):
        raise Verdict.MUMBLE("shared koshecko is broken")

    return res


from pydantic import BaseModel

class FlagData(BaseModel):
    login: str
    password: str
    cat_name: str

ver = Verdict.CHECKER_ERROR("unknown")

@checker.define_vuln("flag_id is koshko")
class CheckChecker(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.ERROR)

        async def lol():
            global ver
            client = api.KoshechkoClient(request.hostname, api.SERVICE_PORT)
            with requests.session() as session:
                fd = await put_flag(client, session, request.flag)
                ver = Verdict.OK_WITH_FLAG_ID(fd.cat_name, fd.model_dump_json())
        
        res = asyncio.run(lol())

        return ver

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.ERROR)

        async def lol():
            global ver
            with ErrorChecker() as ec:
                client = api.KoshechkoClient(request.hostname, api.SERVICE_PORT)
                with requests.session() as session:
                    flag_id_json = FlagData.model_validate_json(request.flag_id)

                    fd = FlagData(
                        login=flag_id_json.login,
                        password=flag_id_json.password,
                        cat_name=flag_id_json.cat_name,
                    )

                    flag = await get_flag(client, session, fd)
                    if request.flag != flag and flag != DELETED:
                        raise Verdict.CORRUPT("Flag not here")
                    
                    ver = Verdict.OK()

        asyncio.run(lol())

        return ver



async def put_flag(client, session, flag) -> FlagData:
    login = generators.random_login()
    password = generators.random_string_in_range(20, 40)
    cat_name = generators.random_cat()

    await client.register(session, login, password)
    token = await client.login(session, login, password)
    session.headers.update({"token": token})

    await client.kosh_create(session, cat_name, flag, [login])
    
    res = await eventually(
        client.kosh_view,
        lambda x: x.rank != 0 and x.score != 0,
        session, cat_name
    )
    if (
        res.name != cat_name or
        res.owner != login or
        res.score != 1 or
        res.text != flag or
        res.shared_with != [login]
    ):
        raise Verdict.MUMBLE("created koshecko is broken")
    
    new_name = generators.random_cat()
    await client.kosh_update(session, cat_name, new_name, flag, [login])

    return FlagData(login=login, password=password, cat_name=new_name)


async def get_flag(client, session, fd: FlagData) -> str:
    token = await client.login(session, fd.login, fd.password)
    session.headers.update({"token": token})

    public_info = generators.random_desc()

    if get_deleted(fd.cat_name):
        return DELETED

    res = await client.kosh_view(
        session, fd.cat_name
    )
    if (
        res.name != fd.cat_name
    ):
        raise Verdict.MUMBLE("old koshecko is broken")

    if random.randint(0, 100) <= 50 and not DISABLE_DELETION:
        await client.kosh_delete(session, fd.cat_name)
        set_deleted(fd.cat_name)
        try:
            res = await eventually(
                client.kosh_view,
                lambda x: x.rank != 0 and x.score != 0,
                session, fd.cat_name
            )
            raise Verdict.MUMBLE("cant delete koshechko")
        except Verdict.ERROR():
            print("error")

    return res.text





if __name__ == "__main__":
    checker.run()
