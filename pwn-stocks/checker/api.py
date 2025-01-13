import asyncio
import aiohttp
import requests

from generators import random_user_agent


SERVICE_PORT: int = 8080
BASE_URL = "http://{hostname}:{port}"
TIMEOUT = 10


sem = asyncio.Semaphore(250)


class TrustedTradingClient:
    def __init__(self, hostname: str, port: int):
        self.hostname = hostname
        self.port = port
        self.token = None

    async def send_post_request_with_random_ua(
        self,
        session: aiohttp.ClientSession | requests.Session,
        endpoint: str,
        data: dict,
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
                ) as response:
                    return await response.json()
            else:
                with session.post(
                    url,
                    json=data,
                    timeout=TIMEOUT,
                ) as response:
                    return response.json()

    async def __send_get_request_with_random_ua(
        self, session: aiohttp.ClientSession, endpoint: str
    ):
        session.headers.update({"User-Agent": random_user_agent()})
        async with sem:
            async with session.get(
                f"{BASE_URL.format(hostname=self.hostname, port=self.port)}/{endpoint}",
                timeout=TIMEOUT,
            ) as response:
                return (response.status, await response.text())

    async def register(
        self,
        session: aiohttp.ClientSession | requests.Session,
        username: str,
        password: str,
    ):
        data = {"username": username, "password": password}
        return await self.send_post_request_with_random_ua(
            session, "api/register", data
        )

    def register_sync(
        self,
        session: requests.Session,
        username: str,
        password: str,
    ):
        return asyncio.run(self.register(session, username, password))

    async def login(
        self,
        session: aiohttp.ClientSession | requests.Session,
        username: str,
        password: str,
    ):
        data = {"username": username, "password": password}
        response = await self.send_post_request_with_random_ua(
            session, "api/login", data
        )
        self.token = response.get("token", None)
        return response

    def login_sync(
        self,
        session: requests.Session,
        username: str,
        password: str,
    ):
        response = asyncio.run(self.login(session, username, password))
        self.token = response.get("token", None)
        return response

    async def submit_trade(
        self,
        session: aiohttp.ClientSession | requests.Session,
        name: str,
        description: str,
        strategy: str,
    ):
        if not self.token:
            raise ValueError("No token provided")
        session.headers.update({"Authorization": f"Bearer {self.token}"})

        data = {"name": name, "description": description, "strategy": strategy}
        return await self.send_post_request_with_random_ua(
            session, "api/user/trade/submit", data
        )

    def submit_trade_sync(
        self, session: requests.Session, name: str, description: str, strategy: str
    ):
        return asyncio.run(self.submit_trade(session, name, description, strategy))

    async def trade_status(
        self, session: aiohttp.ClientSession | requests.Session, trade_id: str
    ):
        if not self.token:
            raise ValueError("No token provided")
        session.headers.update({"Authorization": f"Bearer {self.token}"})

        return await self.send_post_request_with_random_ua(
            session, "api/user/trade/status", {"trade_id": trade_id}
        )

    def trade_status_sync(self, session: requests.Session, trade_id: str):
        return asyncio.run(self.trade_status(session, trade_id))

    async def user_info(self, session: aiohttp.ClientSession | requests.Session):
        if not self.token:
            raise ValueError("No token provided")
        session.headers.update({"Authorization": f"Bearer {self.token}"})

        return await self.send_post_request_with_random_ua(session, "api/user/info", {})

    def user_info_sync(self, session: requests.Session):
        return asyncio.run(self.user_info(session))

    async def trade_history(
        self, session: aiohttp.ClientSession | requests.Session, limit: int
    ):
        return await self.send_post_request_with_random_ua(
            session, "api/trade_history", {"limit": limit}
        )

    def trade_history_sync(self, session: requests.Session, limit: int):
        return asyncio.run(self.trade_history(session, limit))

    async def stock_price(
        self, session: aiohttp.ClientSession | requests.Session, limit: int
    ):
        return await self.send_post_request_with_random_ua(
            session, "api/stock_price", {"limit": limit}
        )

    def stock_price_sync(self, session: requests.Session, limit: int):
        return asyncio.run(self.trade_history(session, limit))

    async def ping(self, session: aiohttp.ClientSession):
        return await self.__send_get_request_with_random_ua(session, "api/ping")

    async def index(self, session: aiohttp.ClientSession):
        return await self.__send_get_request_with_random_ua(session, "index.html")

    async def script(self, session: aiohttp.ClientSession):
        return await self.__send_get_request_with_random_ua(session, "script.js")
