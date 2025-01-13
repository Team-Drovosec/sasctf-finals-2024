import contextlib
import copy
import json
import math
import os
import random
import uuid
from typing import IO
from uuid import UUID

import requests
from bs4 import BeautifulSoup
from checklib import BaseChecker, Status, rnd_string

import config


class ServiceClient:
    def __init__(self, checker: BaseChecker, port: int | str, session: requests.Session):
        self.url = f"http://{checker.host}:{port}"
        self.session = session
        self.checker = checker
        self.remix_presets = {'CUSTOM', 'REVERB', 'BASSBOOST_TAZ', 'DAYCORE', 'NIGHTCORE', 'BASSBOOST_PACAN', 'EARRAPE'}

    def get_form(self) -> None:
        response = self._get(timeout=3)
        self.checker.assert_eq(response.status_code, 200, "Frontend is down", status=Status.DOWN)
        page = BeautifulSoup(response.text, "html.parser")

        preset_selector = page.find("select", {"id": "preset-selector"})
        self.checker.assert_(preset_selector is not None, "Frontend is broken", status=Status.MUMBLE)

        preset_options = set(option.attrs.get("value") for option in preset_selector.find_all("option"))
        self.checker.assert_eq(preset_options, self.remix_presets, "Frontend is broken", status=Status.MUMBLE)

        file_input = page.find("input", {"id": "file"})
        self.checker.assert_(file_input is not None, "Frontend is broken", status=Status.MUMBLE)

        author_input = page.find("input", {"id": "author"})
        self.checker.assert_(author_input is not None, "Frontend is broken", status=Status.MUMBLE)

        button_input = page.find("button", {"id": "make_remix_btn"})
        self.checker.assert_(button_input is not None, "Frontend is broken", status=Status.MUMBLE)

        normalize_input = page.find("input", {"id": "normalize"})
        self.checker.assert_(normalize_input is not None, "Frontend is broken", status=Status.MUMBLE)

    def make_remix_payload(
        self,
        file: IO,
        filename: str | None = None,
        author: str | None = None,
        preset: str | None = None,
        process_cf: list[str] | None = None,
    ) -> tuple[str, dict]:
        _, file_extension = os.path.splitext(file.name)
        if not filename:
            filename = f"{rnd_string(random.randrange(20, 25))}.mp3"
        if not author:
            author = rnd_string(random.randrange(15, 25))
        if process_cf:
            preset = 'CUSTOM'
        if not preset:
            preset = (
                'CUSTOM'
                if random.random() >= 0.5
                else random.choice(list(filter(lambda name: name != 'CUSTOM', self.remix_presets)))
            )
        if preset == 'CUSTOM' and not process_cf:
            process_cf = [
                random.uniform(-10, 10) if random.random() >= 0.7 else f"'{self.__random_expression_for_10_range()}'",  # bass
                random.uniform(-10, 10) if random.random() >= 0.7 else f"'{self.__random_expression_for_10_range()}'",  # volume
                random.uniform(0, 100),  # reverb
                random.uniform(0.5, 2) if random.random() >= 0.7 else f"'({self.__random_expression_from_05_to_2()})'",  # tempo
                random.uniform(-10, 10) if random.random() >= 0.7 else f"'{self.__random_expression_for_10_range()}'",  # treble
                0 if random.random() >= 0.15 else 1,  # normalize
            ]
            possible_indexes_for_zero = [0, 1, 2, 3, 4]
            random.shuffle(possible_indexes_for_zero)
            for i in possible_indexes_for_zero[:3]:
                process_cf[i] = 0
            process_cf = list(map(str, process_cf))
        request_data = {
            "author": author,
            "preset": preset,
        }
        if process_cf and len(process_cf) == 6:
            request_data["process_cf"] = process_cf
        return filename, request_data

    def make_remix(
        self,
        file: IO,
        filename: str,
        params: dict,
    ) -> str:
        process_cf = params.get("process_cf")
        request_data = copy.deepcopy(params)
        if process_cf and len(process_cf) == 6:
            request_data["process_cf"] = json.dumps(process_cf)
        response = self._post(
            "/api/remix/create",
            data=request_data,
            files={"file": (filename, file)},
            timeout=10,
        )
        self.checker.assert_neq(response.status_code, 404, "Failed to create remix", status=Status.DOWN)
        self.checker.assert_eq(response.status_code, 200, "Failed to create remix", status=Status.MUMBLE)
        try:
            UUID(response.text)
        except ValueError:
            self.checker.cquit(Status.MUMBLE, "Failed to create remix")
        return response.text

    def get_meta(self, uuid: str) -> dict:
        response = self._get(f"/api/remix/metadata", params={"name": uuid}, timeout=3)
        self.checker.assert_neq(response.status_code, 404, "Failed to fetch meta", status=Status.DOWN)
        self.checker.assert_eq(response.status_code, 200, "Failed to fetch meta", status=Status.MUMBLE)
        data = response.json()
        meta_keys = ['preset', 'author', 'ts']
        checks = [
            all(key in data for key in meta_keys),
            isinstance(data['author'], str),
            isinstance(data['preset'], str),
            isinstance(data['ts'], int),
        ]
        for check in checks:
            self.checker.assert_(check, "Failed to fetch meta", status=Status.MUMBLE)

        return data

    @contextlib.contextmanager
    def download_file(self, file_id: str) -> str:
        try:
            filename = f"{uuid.uuid4()}.mp3"
            path = os.path.join(config.TEMP_PATH, filename)
            with open(path, 'wb') as file, self._get("/api/file", params={'name': f"{file_id}.mp3"}, stream=True) as response:
                current_iteration = 0
                max_iterations = math.ceil(config.MAX_FILE_SIZE / config.CHUNK_SIZE)
                for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
                    self.checker.assert_gte(max_iterations, current_iteration, "Failed to fetch file", status=Status.MUMBLE)
                    file.write(chunk)
                    current_iteration += 1
            yield path
        finally:
            os.remove(path)

    def _get(self, path: str = "", *args, **kwargs) -> requests.Response:
        return self.session.get(f"{self.url}{path}", *args, **kwargs)

    def _post(self, path: str = "", *args, **kwargs) -> requests.Response:
        return self.session.post(f"{self.url}{path}", *args, **kwargs)

    def _put(self, path: str = "", *args, **kwargs) -> requests.Response:
        return self.session.put(f"{self.url}{path}", *args, **kwargs)

    def _delete(self, path: str = "", *args, **kwargs) -> requests.Response:
        return self.session.delete(f"{self.url}{path}", *args, **kwargs)

    def _patch(self, path: str = "", *args, **kwargs) -> requests.Response:
        return self.session.patch(f"{self.url}{path}", *args, **kwargs)

    def __random_expression_for_10_range(self) -> str:
        expressions = [
            "sin(PI / 2) * 10",
            "cos(0) * 10",
            "tan(PI / 4) * 10",
            "log(E) * 10",
            "sqrt(1e2)",
            "exp(2) - 7.3890561",
            "pow(-1, 1) * 10",
            "sin(PI) * 10",
            "cos(PI) * 10",
            "tan(0) * 10",
            "asin(0.5) * (20 / PI)",
            "acos(0.5) * (-20 / PI) + 10",
            "atan(1) * (10 / (PI / 4))",
            "log(1e4) / log(1e1) - 6",
            "exp(0) * 5 - 5",
            "abs(-10)",
            "ceil(9.1) - 10",
            "floor(-9.1) + 10",
            "round(5.5) - 10",
            "mod(15, 10) - 5",
            "pow(1e1, 0) - 9",
            "(E - 2.7182818) * 10",
            "(PI - 3.1415927) * 10",
            "sqrt(1e2) - 10",
            "hypot(6, 8) - 10",
            "(sin(PI / 6) * 20) - 10",
            "cos(PI / 3) * 10 - 5",
            "tan(PI / 8) * 10",
            "log(1e1) * 10 - 10",
            "exp(2.302585093) - 10",
            "abs(-5) * 2 - 10",
            "pow(2, 3) - 10",
            "pow(1e1, 0.5) - 10",
            "(1 / PI) * 10 - 6.183",
            "(1 / E) * 10 - 6.321",
            "mod(25, 15) - 5",
            "(sin(PI / 4) * 14.1421356) - 10",
            "(cos(PI / 4) * 14.1421356) - 10",
            "tan(1) * 10 - 10",
            "exp(0.69314718) * 5 - 10",
            "pow(27, (1/3)) - 3 - 7",
            "abs(-7.5) - 2.5",
            "ceil(4.5) - 10",
            "floor(-4.5) + 10",
            "round(4.5) - 10",
            "mod(20, 15) - 5",
            "hypot(3, 4) - 5",
            "sin(1) * 10 - 8.4147",
            "cos(1) * 10 - 5.4030",
            "tan(0.5) * 10 - 5.5460",
            "log(1e2) - 4.6052",
            "exp(1) - 10",
            "sqrt(49) - 7 - 3",
            "pow(4, 1.5) - 8",
            "pow(8, (1/3)) - 2 - 8",
            "(PI / E) * 10 - 4.2667",
            "(E / PI) * 10 - 8.6480",
            "abs(cos(PI)) * 10 - 10",
            "sin(PI / 3) * 10 - 8.6603",
            "cos(PI / 6) * 10 - 8.6603",
            "tan(PI / 8) * 10 - 4.1421",
            "log(1e3) / log(1e1) - 10 + 0",
            "exp(2.302585093) - 10",
            "sqrt(64) - 8 - 2",
            "pow(2, 3) - 8 - 2",
            "pow(9, 0.5) - 3 - 7",
            "hypot(5, 12) - 13 + 3",
            "sin(2) * 10 - 9.0929",
            "cos(2) * 10 - 4.1615",
            "tan(0.7) * 10 - 8.422",
            "log(1e1) * 10 - 23.0258",
            "exp(1) - 2.7183 - 7.2817",
            "sqrt(81) - 9 - 1",
            "pow(3, 2) - 9 - 1",
            "pow(16, 0.25) - 2 - 8",
            "(PI - 3) * 10 - 1.4159",
            "(E - 2) * 10 - 7.1828",
            "abs(sin(PI / 2)) * 10 - 10",
            "sin(3 * PI / 2) * 10 + 10",
            "cos(3 * PI / 2) * 10 + 0",
            "tan(PI) * 10 + 0",
            "log(1) * 10 + 0",
            "exp(0) * 10 - 10",
            "sqrt(1e2) - 10 + 0",
            "pow(10, 1) - 10 + 0",
            "pow(100, 0.5) - 10 + 0",
            "abs(-10) - 10 + 0",
            "ceil(9.9) - 10 + 0",
            "floor(-9.9) + 10 + 0",
            "round(9.5) - 10 + 0",
            "mod(20, 30) - 10",
        ]
        return random.choice(expressions).replace(" ", "")

    def __random_expression_from_0_to_100(self) -> str:
        expressions = [
            "(sin(PI / 2) + 1) * 50",
            "(cos(0) + 1) * 50",
            "abs(sin(PI / 2)) * 100",
            "abs(cos(0)) * 100",
            "log(1e2) * 20",
            "sqrt(1e4)",
            "exp(4.60517019)",
            "pow(1e2, 0.5) * 10",
            "(1 - cos(PI / 2)) * 100",
            "(1 + sin(PI / 2)) * 50",
            "abs(sin(PI / 4)) * 100 * sqrt(2) / 2",
            "abs(cos(PI / 4)) * 100 * sqrt(2) / 2",
            "(asin(1) / (PI / 2)) * 100",
            "(acos(0) / (PI / 2)) * 100",
            "(atan(1e2) / (PI / 2)) * 100",
            "log(1e6) / log(1e1) * 10",
            "exp(5) - 1",
            "pow(10, 2)",
            "abs(-100)",
            "ceil(99.1)",
            "floor(99.9)",
            "round(99.5)",
            "mod(200, 100)",
            "(E / E) * 100",
            "(PI / PI) * 100",
            "sqrt(1e4) * 1",
            "hypot(60, 80)",
            "(sin(PI / 6) + 1) * 50",
            "(cos(PI / 3) + 1) * 50",
            "(tan(PI / 4) / 1) * 100 / 2",
            "log(1e5) * 20",
            "exp(4.60517019) - 0",
            "abs(-50) * 2",
            "pow(10, 2)",
            "pow(1e2, 0.5) * 10",
            "(1 / PI) * 100 / 3",
            "(1 / E) * 100 / 2.7182818",
            "mod(250, 150)",
            "(abs(sin(PI / 4)) * 100)",
            "(abs(cos(PI / 4)) * 100)",
            "tan(1) * 100 / 1.5574",
            "exp(3) * 5",
            "pow(1000, 0)",
            "abs(-75) + 25",
            "ceil(49.9) * 2",
            "floor(50.1) * 2",
            "round(49.5) * 2",
            "mod(300, 200)",
            "hypot(30, 40) * 2",
            "abs(sin(1)) * 100 / 0.8415",
            "abs(cos(1)) * 100 / 0.5403",
            "tan(0.5) * 100 / 0.5463",
            "log(1e3) * 20",
            "exp(5) - 1",
            "sqrt(81) * 10",
            "pow(3, 4)",
            "pow(16, 0.5) * 5",
            "(PI / 3) * 100 / PI",
            "(E / 1) * 100 / 2.7182818",
            "abs(cos(0)) * 100",
            "(sin(PI / 3) + 1) * 50",
            "(cos(PI / 6) + 1) * 50",
            "(tan(PI / 4)) * 100 / 1",
            "log(1e4) * 20",
            "exp(4) * 5",
            "sqrt(64) * 10",
            "pow(2, 6)",
            "pow(8, 2)",
            "hypot(6, 8) * 10",
            "abs(sin(2)) * 100 / 0.9093",
            "abs(cos(2)) * 100 / 0.4161",
            "tan(0.7) * 100 / 0.8423",
            "log(1e5) * 20",
            "exp(5) - 1",
            "sqrt(100) * 10",
            "pow(10, 2)",
            "pow(100, 0.5) * 10",
            "(PI - 0) * 100 / PI",
            "(E - 0) * 100 / E",
            "abs(sin(PI / 2)) * 100",
            "abs(sin(3 * PI / 2)) * 100",
            "abs(cos(0)) * 100",
            "tan(PI / 4) * 100 / 1",
            "log(1) * 0 + 50",
            "exp(0) * 100 / 1",
            "sqrt(1e4)",
            "pow(10, 2)",
            "pow(1000, 0.6667)",
            "abs(-100) + 0",
            "ceil(99.9)",
            "floor(0.1)",
            "round(50.5) * 2",
        ]
        return random.choice(expressions).replace(" ", "")

    def __random_expression_from_05_to_2(self) -> str:
        expressions = [
            "(sin(PI / 6) + 1) / 2 + 0.5",
            "(cos(PI / 3) + 1) / 2 + 0.5",
            "(sin(PI / 4) + 1) / 2 + 0.5",
            "(cos(PI / 4) + 1) / 2 + 0.5",
            "(sin(PI / 2) + 1) / 2 + 0.5",
            "(cos(0) + 1) / 2 + 0.5",
            "abs(sin(PI / 3)) + 0.5",
            "abs(cos(PI / 6)) + 0.5",
            "(tan(PI / 8) + 1) / 2 + 0.5",
            "(atan(1) / (PI / 2)) + 0.5",
            "(asin(0.5) / (PI / 2)) + 0.5",
            "(acos(0.5) / (PI / 2)) + 0.5",
            "(log(1e0) + 1) + 0.5",
            "(exp(0) + 0.5)",
            "(sqrt(4) / 2) + 0.5",
            "(pow(2, 0) + 0.5)",
            "(pow(4, 0.5) / 2) + 0.5",
            "(1 / E) + 0.5",
            "(1 / PI) + 0.5",
            "(abs(-1) + 0.5)",
            "(ceil(0.8)) + 0.5",
            "(floor(1.2)) + 0.5",
            "(round(1.5) / 2) + 0.5",
            "(mod(5, 3) / 3) + 0.5",
            "(hypot(0.6, 0.8)) + 0.5",
            "(abs(sin(0.5)) + 0.5)",
            "(abs(cos(0.5)) + 0.5)",
            "(tan(0.25) + 1) / 2 + 0.5",
            "(log(1e1) / log(1e1)) + 0.5",
            "(exp(0.69314718) / 2) + 0.5",
            "(sqrt(9) / 3) + 0.5",
            "(pow(9, 0.5) / 3) + 0.5",
            "(pow(27, (1/3)) / 3) + 0.5",
            "(sin(PI / 6) * 0.5) + 1",
            "(cos(PI / 3) * 0.5) + 1",
            "(abs(sin(PI / 4)) * 0.5) + 1",
            "(abs(cos(PI / 4)) * 0.5) + 1",
            "(tan(PI / 8) * 0.5) + 1",
            "(exp(0.5) / 3) + 0.5",
            "(sqrt(16) / 4) + 0.5",
            "(pow(16, 0.25) / 2) + 0.5",
            "(pow(8, (1/3)) / 2) + 0.5",
            "(abs(-0.5) + 1)",
            "(ceil(0.9)) + 0.5",
            "(floor(1.1)) + 0.5",
            "(round(1.4)) / 2 + 0.5",
            "(mod(7, 5) / 5) + 0.5",
            "(hypot(0.3, 0.4) * 2) + 0.5",
            "(abs(sin(0.7)) + 0.5)",
            "(abs(cos(0.7)) + 0.5)",
            "(tan(0.35) + 1) / 2 + 0.5",
            "(log(1e0) + 1) + 0.5",
            "(exp(0) + 0.5)",
            "(sqrt(25) / 5) + 0.5",
            "(pow(25, 0.5) / 5) + 0.5",
            "(pow(125, (1/3)) / 5) + 0.5",
            "(sin(PI / 4) * 0.5) + 1",
            "(cos(PI / 4) * 0.5) + 1",
            "(abs(sin(PI / 8)) * 0.5) + 1",
            "(abs(cos(PI / 8)) * 0.5) + 1",
            "(tan(PI / 16) * 0.5) + 1",
            "(log(1e1) / 10) + 1",
            "(exp(0.25) / 4) + 0.5",
            "(sqrt(36) / 6) + 0.5",
            "(pow(64, 0.25) / 2) + 0.5",
            "(pow(64, (1/3)) / 4) + 0.5",
            "(abs(-0.75) + 1)",
            "(ceil(0.85)) + 0.5",
            "(floor(1.15)) + 0.5",
            "(round(1.6) / 2) + 0.5",
            "(mod(9, 7) / 7) + 0.5",
            "(hypot(0.5, 0.5) * sqrt(2)) / 2 + 0.5",
            "(abs(sin(0.9)) + 0.5)",
            "(abs(cos(0.9)) + 0.5)",
            "(tan(0.45) + 1) / 2 + 0.5",
            "(log(1e0) + 1) + 0.5",
            "(exp(0) + 0.5)",
            "(sqrt(49) / 7) + 0.5",
            "(pow(49, 0.5) / 7) + 0.5",
            "(pow(343, (1/3)) / 7) + 0.5",
            "(sin(PI / 5) * 0.5) + 1",
            "(cos(PI / 5) * 0.5) + 1",
            "(abs(sin(PI / 10)) * 0.5) + 1",
            "(abs(cos(PI / 10)) * 0.5) + 1",
            "(tan(PI / 20) * 0.5) + 1",
            "(log(1e1) / 20) + 1",
            "(exp(0.125) / 5) + 0.5",
            "(sqrt(64) / 8) + 0.5",
            "(pow(256, 0.25) / 2) + 0.5",
            "(pow(512, (1/3)) / 8) + 0.5",
            "(abs(-1) + 0.5)",
            "(ceil(0.95)) + 0.5",
            "(floor(1.05)) + 0.5",
        ]
        return random.choice(expressions).replace(" ", "")
