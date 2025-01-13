#!/usr/bin/env python3

from collections import namedtuple
from dataclasses import dataclass
from typing import Any
import subprocess
import numpy as np
import sys
import json
import traceback
import aiohttp
import bs4
import requests
import asyncio
import re
import api
import generators

import logging

logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)

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

checker = NewChecker()

DOWN_EXCEPTIONS = {
    client_exceptions.ServerConnectionError,
    client_exceptions.ClientConnectorError,
    client_exceptions.ServerTimeoutError,
    client_exceptions.ServerDisconnectedError,
    client_exceptions.ClientOSError,
    requests.exceptions.ConnectionError,
    requests.exceptions.ProxyError,
    requests.exceptions.Timeout,
    requests.exceptions.ReadTimeout,
    requests.exceptions.TooManyRedirects,
}
MUMBLE_EXCEPTIONS = {
    http_exceptions.HttpProcessingError,
    client_exceptions.ClientResponseError,
    client_exceptions.ContentTypeError,
    client_exceptions.TooManyRedirects,
    json.decoder.JSONDecodeError,
    web_exceptions.HTTPClientError,
    http_exceptions.BadHttpMessage,
    requests.exceptions.JSONDecodeError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ContentDecodingError,
}
KNOWN_EXCEPTIONS = DOWN_EXCEPTIONS | MUMBLE_EXCEPTIONS


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
            print(exc_type)
            print(exc_value.__dict__)
            traceback.print_tb(exc_traceback, file=sys.stdout)
            if exc_type not in KNOWN_EXCEPTIONS:
                raise exc_value

        return True


@dataclass
class Trade:
    net_profit: int
    name: str
    description: str
    strategy: str
    trade_id: str
    strategy_integrity: str
    status: str
    timestamp: str
    stocks_earned: int | None = None

    @staticmethod
    def from_dict(trade: dict):
        try:
            return Trade(
                trade["net_profit"],
                trade["name"],
                trade["description"],
                trade["strategy"],
                trade["trade_id"],
                trade["strategy_integrity"],
                trade["status"],
                trade["timestamp"],
            )
        except KeyError as e:
            raise Verdict.MUMBLE(f"Trade is missing key: {e}")


@dataclass
class StockPrice:
    time: str
    open: int
    close: int
    high: int
    low: int

    @staticmethod
    def from_dict(stock_price: dict):
        try:
            return StockPrice(
                stock_price["time"],
                stock_price["open"],
                stock_price["close"],
                stock_price["high"],
                stock_price["low"],
            )
        except KeyError as e:
            raise Verdict.MUMBLE(f"StockPrice is missing key: {e}")

    def check(self):
        try:
            _ = int(self.time)
        except ValueError as e:
            raise Verdict.MUMBLE("StockPrice time is not valid") from e

        try:
            _ = int(self.open)
        except ValueError as e:
            raise Verdict.MUMBLE("StockPrice open is not valid") from e

        try:
            _ = int(self.close)
        except ValueError as e:
            raise Verdict.MUMBLE("StockPrice close is not valid") from e

        try:
            _ = int(self.high)
        except ValueError as e:
            raise Verdict.MUMBLE("StockPrice high is not valid") from e

        try:
            _ = int(self.low)
        except ValueError as e:
            raise Verdict.MUMBLE("StockPrice low is not valid") from e

        if any(price < 0 for price in [self.open, self.close, self.high, self.low]):
            raise Verdict.MUMBLE("StockPrice contains negative prices")

        if any(price > 1000 for price in [self.open, self.close, self.high, self.low]):
            raise Verdict.MUMBLE("Impossible stock price")


@dataclass
class UserInfo:
    stocks: int
    balance: int
    trades: List[str]

    @staticmethod
    def from_dict(user_info: dict):
        try:
            return UserInfo(
                user_info["stocks"],
                user_info["balance"],
                user_info["trades"],
            )
        except KeyError as e:
            raise Verdict.MUMBLE(f"UserInfo is missing key: {e}")


def check_user_info(actual: UserInfo):
    try:
        _ = int(actual.stocks)
    except ValueError as e:
        raise Verdict.MUMBLE("User stocks is not valid") from e

    try:
        _ = int(actual.balance)
    except ValueError as e:
        raise Verdict.MUMBLE("User balance is not valid") from e

    if actual.stocks < 0:
        raise Verdict.MUMBLE("User stocks is negative")

    if actual.balance < 0:
        raise Verdict.MUMBLE("User balance is negative")

    if not all(is_valid_uuid(trade_id) for trade_id in actual.trades):
        raise Verdict.MUMBLE("User trades contain invalid trade IDs")


def check_trade(expected: Trade, actual: Trade):
    try:
        _ = int(actual.net_profit)
    except ValueError as e:
        raise Verdict.MUMBLE("Trade net profit is not valid") from e

    if expected.net_profit != actual.net_profit:
        raise Verdict.MUMBLE("Trade net profit mismatch")

    if expected.name != actual.name:
        raise Verdict.MUMBLE("Trade name mismatch")

    if expected.description != actual.description:
        raise Verdict.MUMBLE("Trade description mismatch")

    if expected.strategy != actual.strategy:
        raise Verdict.MUMBLE("Trade strategy mismatch")

    if expected.trade_id != actual.trade_id:
        raise Verdict.MUMBLE("Trade ID mismatch")

    if is_valid_uuid(expected.trade_id) is False:
        raise Verdict.MUMBLE("Trade ID is not valid")

    if expected.strategy_integrity != actual.strategy_integrity:
        raise Verdict.MUMBLE("Trade integrity mismatch")

    if len(actual.strategy_integrity) != 64:
        raise Verdict.MUMBLE("Trade integrity is not valid")

    if expected.status != actual.status:
        raise Verdict.MUMBLE("Trade status mismatch")

    if actual.status not in ["pending", "completed", "failed"]:
        raise Verdict.MUMBLE("Trade status is not valid")

    if expected.timestamp != actual.timestamp:
        raise Verdict.MUMBLE("Trade timestamp mismatch")

    try:
        _ = int(actual.timestamp)
    except ValueError as e:
        raise Verdict.MUMBLE("Trade timestamp is not valid") from e


class Trader:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.stocks = 1
        self.balance = 100000
        self.trades: List[Trade] = []

    def add_trade(self, trade: Trade):
        self.trades.append(trade)

    def __str__(self):
        return f"Trader(username={self.username}, password={self.password}, stocks={self.stocks}, balance={self.balance}, trades={self.trades})"


EvaluationResult = namedtuple("EvaluationResult", ["result", "integrity", "error"])


def evaluate_expression(expression: str) -> EvaluationResult:
    output = subprocess.check_output(
        ["./integrity_calculator", f"{expression}"],
        stderr=subprocess.STDOUT,
    )

    output = output.decode("utf-8").strip().splitlines()

    if len(output) == 1:
        return EvaluationResult(None, None, output[0])

    integrity = next(
        line for line in output if line.startswith("Code integrity:")
    ).split(": ")[1]
    result = int(
        next(line for line in output if line.startswith("Result:")).split(": ")[1]
    )

    return EvaluationResult(result, integrity, None)


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def check_error(error: dict[str, str], expected_message: str, mumble_reason: str):
    if "message" not in error or error["message"] != expected_message:
        raise Verdict.MUMBLE(mumble_reason)


def re_check_error(error: dict[str, str], expected_message: str, mumble_reason: str):
    if "message" not in error or re.match(expected_message, error["message"]) is None:
        raise Verdict.MUMBLE(mumble_reason)


async def do_test_ping(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession
):
    # Check /ping

    pong = await client.ping(session)
    if pong[0] != 200:
        raise Verdict.MUMBLE("ping failed")


async def do_test_frontend(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession
):
    # Check /index.html

    response = await client.index(session)
    raw_html = response[1]
    soup = bs4.BeautifulSoup(raw_html, "html.parser")

    if not soup.title or soup.title.string != "stocks++":
        raise Verdict.MUMBLE("Invalid title")

    response = await client.script(session)
    raw_html = response[1]

    substrings = [
        "Users Trade History",
        "Welcome to stocks++",
        "Trade ID",
        "Net Profit",
        "Strategy Name",
        "Strategy Description",
        "Strategy Code",
        "Stock Prices",
        "Username",
        "Password",
    ]
    for substring in substrings:
        if substring not in raw_html:
            raise Verdict.MUMBLE("Frontend is corrupted!")


async def do_test_register(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession
) -> Trader:
    # Check /api/register

    # Check empty json
    error = await client.send_post_request_with_random_ua(session, "api/register", {})
    check_error(
        error,
        "Error at path 'username': Field is missing",
        "Register: Incorrect response for malformed json",
    )

    # Check json with missing field
    error = await client.send_post_request_with_random_ua(
        session,
        "api/register",
        {"username": generators.random_string_in_range(10, 60)},
    )
    check_error(
        error,
        "Error at path 'password': Field is missing",
        "Register: Incorrect response for malformed json",
    )

    # Check json with incorrect type of description
    error = await client.send_post_request_with_random_ua(
        session,
        "api/register",
        {
            "username": generators.random_string_in_range(10, 60),
            "password": generators.random_int_exclude([], 1, 2**32),
        },
    )
    re_check_error(
        error,
        "Error at path 'password': Wrong type. Expected: stringValue, actual: intValue",
        "Register: Incorrect response for malformed json",
    )

    # Check user with empty username can't be added
    username = ""
    password = generators.random_string_in_range(10, 60)
    error = await client.register(session, username, password)
    check_error(
        error,
        "Username is empty",
        "Register: Incorrect response for empty username",
    )

    # Check user with too long username can't be added
    username = generators.random_string_in_range(65, 255)
    password = generators.random_string_in_range(10, 60)
    error = await client.register(session, username, password)
    check_error(
        error,
        "Username is too long",
        "Register: Incorrect response for too long username",
    )

    # Check user with empty password can't be added
    username = generators.random_string_in_range(10, 60)
    password = ""
    error = await client.register(session, username, password)
    check_error(
        error,
        "Password is empty",
        "Register: Incorrect response for empty password",
    )

    # Check user with too long password can't be added
    username = generators.random_string_in_range(10, 60)
    password = generators.random_string_in_range(65, 255)
    error = await client.register(session, username, password)
    check_error(
        error,
        "Password is too long",
        "Register: Incorrect response for too long password",
    )

    # Check correct user can be added
    username = generators.random_string_in_range(10, 30)
    password = generators.random_string_in_range(10, 60)
    message = await client.register(session, username, password)
    check_error(
        message,
        f"User {username} registered successfully",
        "Register: Incorrect response for correct user",
    )

    # Check the same user can't be added
    error = await client.register(session, username, password)
    check_error(
        error,
        "User already exists",
        "Register: Incorrect response for duplicate user",
    )

    return Trader(username, password)


async def do_test_login(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession, trader: Trader
):
    # Check /api/login

    # Make sure random username can't be logged in
    username = generators.random_string_in_range(10, 60)
    password = generators.random_string_in_range(10, 60)
    error = await client.login(session, username, password)
    check_error(
        error,
        "Invalid username or password",
        "Login: Incorrect response for random user",
    )

    # Make sure too long password can't be logged in
    username = generators.random_string_in_range(10, 60)
    password = generators.random_string_in_range(65, 255)
    error = await client.login(session, username, password)
    check_error(
        error,
        "Password is too long",
        "Login: Incorrect response for too long password",
    )

    # Make sure too long username can't be logged in
    username = generators.random_string_in_range(65, 255)
    password = generators.random_string_in_range(10, 60)
    error = await client.login(session, username, password)
    check_error(
        error,
        "Username is too long",
        "Login: Incorrect response for too long username",
    )

    # Make sure correct user can be logged in
    token = await client.login(session, trader.username, trader.password)
    if "token" not in token or len(token["token"]) == 0:
        raise Verdict.MUMBLE("Login: Incorrect response for correct user")

    return token


def calculable_expression(max_iters=1000) -> tuple[Any, bool]:
    for _ in range(max_iters):
        strategy = generators.random_expression(
            generators.random_int_exclude([], 3, 6),
            [],
            ["+", "-", "*", "/"],
            [0.45, 0.3, 0.1, 0.15],
        )
        try:
            result = eval(str(strategy))
        except Exception:
            continue

        if result > 0 and result * 10 < 100_000 // 350:
            return strategy, True

    return strategy, False


async def do_test_trade_submit(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession, trader: Trader
):
    # Check /api/user/trade/submit
    def expr():
        is_calculateable = False
        strategy = ""
        match np.random.randint(0, 3):
            case 0:
                strategy = generators.random_expression(
                    generators.random_int_exclude([], 3, 18),
                    ["BALANCE", "STOCK_PRICE", "HOLDINGS", "HOLDINGS_VALUE"],
                )
            case 1:
                if np.random.randint(0, 2):
                    strategy = generators.deeply_nested_expression_left(
                        generators.random_int_exclude([], 30, 1000),
                        ["BALANCE", "STOCK_PRICE", "HOLDINGS", "HOLDINGS_VALUE"],
                    )
                else:
                    strategy = generators.deeply_nested_expression_right(
                        generators.random_int_exclude([], 30, 1000),
                        ["BALANCE", "STOCK_PRICE", "HOLDINGS", "HOLDINGS_VALUE"],
                    )
            case 2:
                # Simple, calculateable expression
                strategy, is_calculateable = calculable_expression()
        return str(strategy), is_calculateable

    # Check trade with empty name can't be created
    name = ""
    description = generators.random_string_in_range(10, 60)
    strategy, _ = expr()
    trade = await client.submit_trade(session, name, description, strategy)
    check_error(
        trade,
        "Trade name is empty",
        "TradeSubmit: Incorrect response for empty name",
    )

    # Check trade with too long name can't be created
    name = generators.random_string_in_range(260, 300)
    description = generators.random_string_in_range(10, 60)
    strategy, _ = expr()
    trade = await client.submit_trade(session, name, description, strategy)
    check_error(
        trade,
        "Trade name is too long",
        "TradeSubmit: Incorrect response for too long name",
    )

    # Check trade with empty description can't be created
    name = generators.random_string_in_range(10, 60)
    description = ""
    strategy, _ = expr()
    trade = await client.submit_trade(session, name, description, strategy)
    check_error(
        trade,
        "Trade description is empty",
        "TradeSubmit: Incorrect response for empty description",
    )

    # Check trade with too long description can't be created
    name = generators.random_string_in_range(10, 60)
    description = generators.random_string_in_range(260, 300)
    strategy, _ = expr()
    trade = await client.submit_trade(session, name, description, strategy)
    check_error(
        trade,
        "Trade description is too long",
        "TradeSubmit: Incorrect response for too long description",
    )

    # Check trade with empty strategy can't be created
    name = generators.random_string_in_range(10, 60)
    description = generators.random_string_in_range(10, 60)
    strategy = ""
    trade = await client.submit_trade(session, name, description, strategy)
    check_error(
        trade,
        "Trade strategy is empty",
        "TradeSubmit: Incorrect response for empty strategy",
    )

    # Check trade with broken strategy can't be created
    name = generators.random_string_in_range(10, 60)
    description = generators.random_string_in_range(10, 60)
    strategy, _ = expr()
    trade = await client.submit_trade(session, name, description, strategy + ")")
    check_error(
        trade,
        "Failed to compile strategy: Failed to convert the input to RPN: Mismatched closing parenthesis",
        "TradeSubmit: Incorrect response for broken strategy",
    )

    # Check correct trade can be created
    name = generators.random_string_in_range(10, 60)
    description = generators.random_string_in_range(10, 60)
    strategy, is_calculateable = expr()
    trade = Trade.from_dict(
        await client.submit_trade(session, name, description, strategy)
        | {
            "net_profit": 0,
            "name": name,
            "description": description,
            "strategy": strategy,
            "status": "pending",
            "timestamp": "-",
        }
    )
    result = evaluate_expression(trade.strategy)

    # If the strategy is simple enough, and won't use more than 100_000 balance, calculate the stocks earned
    if is_calculateable and result.result > 0 and result.result * 10 < 100_000 // 350:
        # print(f"{strategy} = {result.result}")
        trade.stocks_earned = result.result * 10 + 1

    trader.add_trade(trade)

    # Give some time for the trade to be processed
    await asyncio.sleep(2)

    # Make sure the trade is in the trade history
    history = await client.trade_history(session, 100)
    if "trades" not in history:
        raise Verdict.MUMBLE("Trade not in trade history")

    for trade in history["trades"]:
        trade = Trade.from_dict(
            trade | {"name": name, "description": description, "strategy": strategy}
        )
        # This is a bit hacky, but it's done to run some checks on the trade
        check_trade(trade, trade)
        if trade.trade_id == trader.trades[0].trade_id:
            break
    else:
        raise Verdict.MUMBLE("Trade not in trade history")

    if result.integrity != trade.strategy_integrity:
        raise Verdict.MUMBLE("Trade integrity mismatch")

    if is_valid_uuid(trade.trade_id) is False:
        raise Verdict.MUMBLE("Trade ID is not valid")

    # Check another trade can't be created right after the first one
    name = generators.random_string_in_range(10, 60)
    description = generators.random_string_in_range(10, 60)
    strategy, _ = expr()
    message = await client.submit_trade(session, name, description, strategy)
    check_error(
        message,
        "You already have a pending trade!",
        "TradeSubmit: Incorrect response for simultaneous trades",
    )


async def do_test_trade_status(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession, trader: Trader
):
    # Check /api/user/trade/status

    # Check another trade can't be created right after the first one
    trade_id = generators.random_invalid_uuid4()
    message = await client.trade_status(session, trade_id)
    check_error(
        message,
        "Invalid trade_id",
        "TradeStatus: Incorrect response for invalid trade_id",
    )

    # Check another trade can't be created right after the first one
    trade_id = generators.random_uuid4()
    message = await client.trade_status(session, trade_id)
    check_error(
        message,
        "Trade not found",
        "TradeStatus: Incorrect response for non-existent trade",
    )

    # Wait for the trade to be completed
    await asyncio.sleep(12)

    original_trade = trader.trades[0]
    trade = await client.trade_status(session, original_trade.trade_id)
    trade = Trade.from_dict(trade | {"trade_id": original_trade.trade_id})

    if original_trade.stocks_earned is not None:
        # Wait for the trade to be completed? WTF, seems that sometimes
        # 12 seconds is not enough?
        for _ in range(3):
            if trade.status == "completed":
                break

            trade = await client.trade_status(session, original_trade.trade_id)
            trade = Trade.from_dict(trade | {"trade_id": original_trade.trade_id})
            await asyncio.sleep(2)
        else:
            raise Verdict.MUMBLE("TradeStatus: Trade status is not correct")

    # set the timestamp and status to the one returned by the server
    original_trade.timestamp = trade.timestamp
    original_trade.status = trade.status
    original_trade.net_profit = trade.net_profit

    check_trade(original_trade, trade)


async def do_test_user_info(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession, trader: Trader
):
    # Check /api/user/info
    user_info = await client.user_info(session)
    user_info = UserInfo.from_dict(user_info)
    check_user_info(user_info)

    original_trade = trader.trades[0]
    if original_trade.trade_id != user_info.trades[0]:
        raise Verdict.MUMBLE("UserInfo: Trade id from user info is incorrect")

    # Stocks earned is easily calculable (cause the strategy is simple) - check if it matches
    if original_trade.stocks_earned is not None:
        if user_info.stocks != original_trade.stocks_earned:
            # print(f"Stocks: {user_info.stocks}, {original_trade.stocks_earned}")
            # print(trader)
            raise Verdict.MUMBLE("UserInfo: Stocks earned mismatch")


async def do_test_trade_history(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession
):
    # Check /api/trade_history
    # Done in do_test_trade_submit
    pass


async def do_test_stock_price(
    client: api.TrustedTradingClient, session: aiohttp.ClientSession
):
    # Check /api/stock_price
    stock_prices = await client.stock_price(session, 27)
    if "prices" not in stock_prices:
        raise Verdict.MUMBLE("Stock prices not found")

    if len(stock_prices["prices"]) != 27:
        raise Verdict.MUMBLE("Stock prices count mismatch")

    for stock_price in stock_prices["prices"]:
        stock_price = StockPrice.from_dict(stock_price)
        stock_price.check()


@checker.define_check
async def check_service(request: CheckRequest) -> Verdict:
    with ErrorChecker() as ec:
        client = api.TrustedTradingClient(request.hostname, api.SERVICE_PORT)
        async with aiohttp.ClientSession() as session:
            # Check /ping
            await do_test_ping(client, session)

            # Check frontend
            await do_test_frontend(client, session)

            # Check /api/register
            trader = await do_test_register(client, session)

            # Check /api/login
            await do_test_login(client, session, trader)

            # Check /api/user/trade/submit
            await do_test_trade_submit(client, session, trader)

            # Check /api/user/trade/status
            await do_test_trade_status(client, session, trader)

            # Check /api/user/info
            await do_test_user_info(client, session, trader)

            # Check /api/trade_history
            # await do_test_trade_history(client, session, trader)

            # Check /api/stock_price
            await do_test_stock_price(client, session)

            ec.verdict = Verdict.OK()

    return ec.verdict


@checker.define_vuln("flag_id is the description")
class BitSetOverflowChecker(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        with ErrorChecker() as ec:
            client = api.TrustedTradingClient(request.hostname, api.SERVICE_PORT)
            with requests.session() as session:
                username = generators.random_string_in_range(10, 60)
                password = generators.random_string_in_range(10, 60)
                message = client.register_sync(session, username, password)
                check_error(
                    message,
                    f"User {username} registered successfully",
                    "Register: Incorrect response for correct user",
                )

                token = client.login_sync(session, username, password)
                if "token" not in token or len(token["token"]) == 0:
                    raise Verdict.MUMBLE("Login: Incorrect response for correct user")

                trade_name = generators.random_string_in_range(10, 60)
                trade_description = request.flag
                trade_strategy = str(
                    generators.random_expression(
                        generators.random_int_exclude([], 3, 18),
                        ["BALANCE", "STOCK_PRICE", "HOLDINGS", "HOLDINGS_VALUE"],
                    )
                )
                trade = Trade.from_dict(
                    client.submit_trade_sync(
                        session, trade_name, trade_description, trade_strategy
                    )
                    | {
                        "net_profit": 0,
                        "name": trade_name,
                        "description": trade_description,
                        "strategy": trade_strategy,
                        "status": "pending",
                        "timestamp": "-",
                    }
                )

                flag_id = json.dumps(
                    {
                        "username": username,
                        "password": password,
                        "trade_id": trade.trade_id,
                    }
                )
                ec.verdict = Verdict.OK_WITH_FLAG_ID(trade.trade_id, flag_id)

        return ec.verdict

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        with ErrorChecker() as ec:
            client = api.TrustedTradingClient(request.hostname, api.SERVICE_PORT)
            with requests.session() as session:
                flag_id_json = json.loads(request.flag_id)
                username = flag_id_json["username"]
                password = flag_id_json["password"]

                token = client.login_sync(session, username, password)
                if "token" not in token or len(token["token"]) == 0:
                    raise Verdict.MUMBLE("Login: Incorrect response for correct user")

                # Check if the flag can be correctly extracted by viewing the trade
                try:
                    trade = Trade.from_dict(
                        client.trade_status_sync(session, flag_id_json["trade_id"])
                        | {"trade_id": flag_id_json["trade_id"]}
                    )
                except Verdict as v:
                    raise Verdict.CORRUPT(
                        f"Strategy status failed: {v._public_message}"
                    )

                if trade.description != request.flag:
                    raise Verdict.CORRUPT("Flag mismatch")

        return ec.verdict


if __name__ == "__main__":
    checker.run()
