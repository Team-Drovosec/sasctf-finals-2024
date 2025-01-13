import asyncio
import aiohttp
import requests
import json

from typing import (
    List
)

from generators import (
    generate_random_bitfield,
    generate_random_bitrow,
    random_user_agent,
    random_text
)

from models import *

class ErrorCode(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(self.code)

    def __str__(self):
        return f"Error code: {self.code}"



SERVICE_PORT: int = 3134
BASE_URL = "http://{hostname}:{port}"
TIMEOUT = 10


sem = asyncio.Semaphore(250)


class KoshechkoClient:
    def __init__(self, hostname: str, port: int):
        self.hostname = hostname
        self.port = port

    async def send_post_request_with_random_ua(
        self,
        session: aiohttp.ClientSession | requests.Session,
        endpoint: str,
        data: dict,
        headers: dict = {}
    ):
        session.headers.update({"User-Agent": random_user_agent()})
        async with sem:
            url = (
                f"{BASE_URL.format(hostname=self.hostname, port=self.port)}/{endpoint}"
            )
            if isinstance(session, aiohttp.ClientSession):
                async with session.post(
                    url,
                    json=data,
                    timeout=TIMEOUT,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return response.status, None
                    json = await response.json()
                    return (response.status, json)

            else:
                with session.post(
                    url,
                    json=data,
                    timeout=TIMEOUT,
                    headers=headers
                ) as response:
                    return (response.status_code, response.json())


    async def send_get_request_with_random_ua(
        self, session: aiohttp.ClientSession, endpoint: str
    ):
        session.headers.update({"User-Agent": random_user_agent()})
        async with sem:
            async with session.get(
                f"{BASE_URL.format(hostname=self.hostname, port=self.port)}/{endpoint}",
                timeout=TIMEOUT,
            ) as response:
                if response.status != 200:
                    return response.status, None
                    
                return (response.status, await response.text())

    async def register(
        self,
        session: aiohttp.ClientSession | requests.Session,
        login: str,
        password: str
    ):
        req = {"username": login, "password": password, "desc": random_text()}
        code, resp = await self.send_post_request_with_random_ua(session, "api/register", req)
        if code != 200:
            raise ErrorCode(code)
        
        return

    def calc_hash(self, tx: str):
        e = 65537
        n = 28757011453696365537010943219256697514126823462382199267523807215656057927126938852532938273735278647439093723114415999527098723727976475936319155015427799997213003664499422631017367287332875193524677851189982495235297707215042033048262623778358190536462998154798211571895963976626619781876160386784876909081999350085274414471035318193235136484576917339366720845318413892930365483764728962401235587394114713997688753422002084296070311024847072828816942070893651675293360209965132732838522510660772870550822829094375086110109463351493357171504313446493634012225805624774006426508038811853036507008224435127381274346463
        p = 1        
        for x in tx:
            p *= ord(x)
        return str(pow(p, e, n))

    async def login(
        self,
        session: aiohttp.ClientSession | requests.Session,
        login: str,
        password: str
    ) -> str:
        code, resp = await self.send_post_request_with_random_ua(session, "api/identify", {"username": login})
        if code != 200:
            raise ErrorCode(code)
        

        tok = resp["token"]
        sess_token = resp["session"]

        code, resp = await self.send_post_request_with_random_ua(
            session,
            "api/login",
            {"password": self.calc_hash(password + tok)},
            headers={"token": sess_token}
        )
        if code != 200:
            raise ErrorCode(code)
        return sess_token

    async def top_koshechko(
        self,
        session: aiohttp.ClientSession | requests.Session,
    ) -> List[KoshechkoTop]:
        code, resp = await self.send_get_request_with_random_ua(session, "api/top/koshechko")
        if code != 200:
            raise ErrorCode(code)
        
        res = json.loads(resp)
        res = [KoshechkoTop(name=x["name"], rank=x["rank"], score=x["score"]) for x in res["top"]]
        
        return res
    
    async def top_users(
        self,
        session: aiohttp.ClientSession | requests.Session,
    ) -> List[UserTop]:
        code, resp = await self.send_get_request_with_random_ua(session, "api/top/users")
        if code != 200:
            raise ErrorCode(code)
        
        res = json.loads(resp)
        res = [UserTop(name=x["username"], rank=x["rank"], score=x["score"]) for x in res["top"]]
        
        return res

    async def kosh_create(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
        text: str,
        shared_with: List[str]
    ):
        req = {"name": name, "text": text, "shared_with": shared_with}
        code, resp = await self.send_post_request_with_random_ua(session, "api/koshechko/create", req)
        if code != 200:
            raise ErrorCode(code)
        
        return

    async def kosh_update(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
        new_name: str,
        text: str,
        shared_with: List[str]
    ):
        req = {"name": name, "new_name": new_name, "text": text, "shared_with": shared_with}
        code, resp = await self.send_post_request_with_random_ua(session, "api/koshechko/update", req)
        if code != 200:
            raise ErrorCode(code)
        
        return

    async def kosh_delete(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
    ):
        req = {"name": name}
        code, resp = await self.send_post_request_with_random_ua(session, "api/koshechko/delete", req)
        if code != 200:
            raise ErrorCode(code)
        
        return

    async def kosh_view(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
    ):
        req = {"name": name}
        code, resp = await self.send_post_request_with_random_ua(session, "api/koshechko/view", req)
        if code != 200:
            raise ErrorCode(code)
        
        return Koshechko(
            name=resp["name"],
            owner=resp["owner"],
            text=resp["text"],
            rank=int(resp["rank"]),
            score=int(resp["score"]),
            shared_with=resp["shared_with"]
        )

    async def user_view(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
    ):
        req = {"name": name}
        code, resp = await self.send_post_request_with_random_ua(session, "api/user/view", req)
        if code != 200:
            raise ErrorCode(code)
        
        return User(
            name=resp["name"],
            desc=resp["desc"],
            rank=int(resp["rank"]),
        )

    async def user_update(
        self,
        session: aiohttp.ClientSession | requests.Session,
        desc: str,
    ):
        req = {"desc": desc}
        code, resp = await self.send_post_request_with_random_ua(session, "api/user/update", req)
        if code != 200:
            raise ErrorCode(code)
        return

    async def user_delete(
        self,
        session: aiohttp.ClientSession | requests.Session,
    ):
        code, resp = await self.send_post_request_with_random_ua(session, "api/user/delete", {})
        if code != 200:
            raise ErrorCode(code)
        return
