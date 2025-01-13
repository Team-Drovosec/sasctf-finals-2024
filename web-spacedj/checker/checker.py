#!/bin/env python3.12

import asyncio
import json
import os
import random
import sys
from typing import IO

import requests
from checklib import *
from checklib import status
from pydub import AudioSegment
from pydub.utils import mediainfo_json

import config
from helpers import generate_audio, make_local_remix, compare_audio_files
from service_client import ServiceClient


class Checker(BaseChecker):
    down_exceptions = {
        requests.exceptions.ConnectionError,
        requests.exceptions.ProxyError,
        requests.exceptions.Timeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.TooManyRedirects,
    }
    mumble_exceptions = {
        requests.exceptions.JSONDecodeError,
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ContentDecodingError,
        json.decoder.JSONDecodeError,
    }

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        session = self._get_session()
        self.service_client = ServiceClient(checker=self, port=config.SERVICE_PORT, session=session)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except Exception as exc:
            exc_type = type(exc)
            if exc_type in self.down_exceptions:
                self.cquit(Status.DOWN, "Service is down", private=str(exc_type))
            if exc_type in self.mumble_exceptions:
                self.cquit(Status.MUMBLE, "Service is mumbled", private=str(exc_type))
            raise

    def check(self):
        self.service_client.get_form()
        with generate_audio() as audio_file:
            filename, payload = self.service_client.make_remix_payload(audio_file)
            audio_id, audio_payload = self.create_audio(audio_file, filename, payload)
            with self.service_client.download_file(audio_id) as remote_audio_path:
                with make_local_remix(remote_audio_path, audio_payload) as local_audio_path:
                    self.equal_audio_files(remote_audio_path, local_audio_path)
                pass
        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        with generate_audio(flag) as audio_file:
            filename, payload = self.service_client.make_remix_payload(audio_file)
            audio_id, _ = self.create_audio(audio_file, filename, payload)
        self.cquit(Status.OK, private=audio_id)

    def get(self, flag_id: str, flag: str, vuln: str):
        with self.service_client.download_file(flag_id) as remote_audio_path:
            try:
                mediainfo = mediainfo_json(remote_audio_path)
            except Exception as exc:
                self.cquit(Status.MUMBLE, "Corrupted remix file", private=str(exc))
            self.assert_in("format", mediainfo, "Corrupted remix file", Status.CORRUPT)
            format_section = mediainfo["format"]
            self.assert_in("tags", format_section, "Corrupted remix file", Status.CORRUPT)
            tags = format_section["tags"]
            self.assert_in("title", tags, "Corrupted remix file", Status.CORRUPT)
            flag_in_file = tags["title"]
            self.assert_eq(flag_in_file, flag, "Corrupted remix file", Status.CORRUPT)
        self.cquit(Status.OK)

    def create_audio(self, audio_file: IO, filename: str, payload: dict) -> tuple[str, dict]:
        file_uuid = self.service_client.make_remix(audio_file, filename, payload)
        meta = self.service_client.get_meta(file_uuid)
        self.assert_eq(meta['author'], payload['author'], "Corrupted remix info", Status.MUMBLE)
        self.assert_eq(meta['preset'], payload['preset'], "Corrupted remix info", Status.MUMBLE)
        return file_uuid, payload

    def equal_audio_files(self, reference_file: str, against_file: str) -> None:
        self.assert_gte(
            config.AUDIO_COMPARISON_TOLERANCE,
            compare_audio_files(reference_file, against_file),
            "Corrupted remix file",
            Status.MUMBLE,
        )

    def _get_session(self) -> requests.Session:
        sess = requests.Session()
        sess.headers["User-Agent"] = random.choice(config.USER_AGENTS)
        return sess


if __name__ == '__main__':
    c = Checker(sys.argv[2])
    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception() as e:
        cquit(status.Status(c.status), c.public, c.private)
