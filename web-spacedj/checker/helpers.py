import contextlib
import os
import random
import uuid
from functools import lru_cache
from typing import BinaryIO, IO
import dj
from enum import StrEnum

import librosa
from checklib import rnd_string
from dtw import dtw
from librosa.feature import mfcc
from pydub import AudioSegment

import config


class Preset(StrEnum):
    BASSBOOST_TAZ = "BASSBOOST_TAZ"
    BASSBOOST_PACAN = "BASSBOOST_PACAN"
    NIGHTCORE = "NIGHTCORE"
    DAYCORE = "DAYCORE"
    REVERB = "REVERB"
    EARRAPE = "EARRAPE"
    CUSTOM = "CUSTOM"


@contextlib.contextmanager
def generate_audio(flag: str | None = None, min_sounds: int = 8, max_sounds: int = 14) -> IO:
    file_name = f"{uuid.uuid4()}.mp3"
    file_path = os.path.join(config.TEMP_PATH, file_name)
    try:
        audio = generate_audio_sample(min_sounds, max_sounds)
        audio.export(
            file_path,
            format='mp3',
            tags={'title': flag} if flag else None,
        )
        with open(file_path, "rb") as audio_file:
            yield audio_file
    finally:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass


@lru_cache
def get_drum_loop_paths() -> list[str]:
    return list(filter(lambda name: name.endswith(".mp3"), os.listdir(config.DRUM_LOOPS_PATH)))


@lru_cache
def get_sound_paths() -> list[str]:
    return list(filter(lambda name: name.endswith(".mp3"), os.listdir(config.SOUNDS_PATH)))


def generate_audio_sample(min_sounds=8, max_sounds=14) -> AudioSegment:
    drum_loop_path = random.choice(get_drum_loop_paths())
    sound_paths = random.choices(get_sound_paths(), k=random.randint(min_sounds, max_sounds))

    drum_loop = AudioSegment.from_mp3(os.path.join(config.DRUM_LOOPS_PATH, drum_loop_path))
    drum_loop_len = len(drum_loop) // 1000
    second_steps = [i for i in range(0, drum_loop_len, 2)]
    for sound_path in sound_paths:
        sound = AudioSegment.from_mp3(os.path.join(config.SOUNDS_PATH, sound_path))
        sound_len = len(sound) // 1000
        valid_steps = [i for i in second_steps if (drum_loop_len - i) >= sound_len]
        if not valid_steps:
            position = random.randint(0, max(0, drum_loop_len - sound_len))
        else:
            position = random.choice(valid_steps)
            second_steps.remove(position)
        drum_loop = drum_loop.overlay(
            sound,
            position=position * 1000,
        )
    return drum_loop


@contextlib.contextmanager
def make_local_remix(file_path_in: str, payload: dict) -> str:
    """
    payload variants:
    {
        'author': '324tFHCRnSJ42TV',
        'preset': 'CUSTOM',
        'process_cf': ['2.9017992770979344', "'round(4.5)-10'", '55.08147757746197', "'((ceil(0.95))+0.5)'", "'ceil(9.1)-10'", '1'],
    }
    {
        'author': 'UXizMSbHxYAneLCZt3XC',
        'preset': 'EARRAPE'
    }
    """
    try:
        file_name = f"{uuid.uuid4()}.mp3"
        file_path_out = os.path.join(config.TEMP_PATH, file_name)
        match payload['preset']:
            case Preset.BASSBOOST_TAZ:
                res = dj.bassboost_taz(file_path_in, file_path_out)
            case Preset.BASSBOOST_PACAN:
                res = dj.bassboost_pacan(file_path_in, file_path_out)
            case Preset.NIGHTCORE:
                res = dj.nightcore(file_path_in, file_path_out)
            case Preset.DAYCORE:
                res = dj.daycore(file_path_in, file_path_out)
            case Preset.REVERB:
                res = dj.reverb(file_path_in, file_path_out)
            case Preset.EARRAPE:
                res = dj.earrape(file_path_in, file_path_out)
            case Preset.CUSTOM:
                res = dj.custom(file_path_in, file_path_out, payload['process_cf'])
        yield file_path_out
    finally:
        os.remove(file_path_out)


def compare_audio_files(reference_file: str, against_file: str) -> float:
    y1, sr1 = librosa.load(reference_file)
    y2, sr2 = librosa.load(against_file)

    mfcc1 = mfcc(y=y1, sr=sr1)
    mfcc2 = mfcc(y=y2, sr=sr2)
    check = dtw(mfcc1.T, mfcc2.T)
    print(check.normalizedDistance)
    return check.normalizedDistance
