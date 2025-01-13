import asyncio
import json
import time
import uuid
import os
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from enum import StrEnum

import core.dj as dj
from aiohttp.web_request import FileField

from core.aioredis import RedisProvider
from settings import get_app_settings


class Preset(StrEnum):
    BASSBOOST_TAZ = "BASSBOOST_TAZ"
    BASSBOOST_PACAN = "BASSBOOST_PACAN"
    NIGHTCORE = "NIGHTCORE"
    DAYCORE = "DAYCORE"
    REVERB = "REVERB"
    EARRAPE = "EARRAPE"
    CUSTOM = "CUSTOM"


def process_upload(content: bytes, name_in: str, name_out: str, preset: str, cf: list[str] | None) -> tuple[bool, str]:
    path_in = f'/app/uploads/{name_in}.mp3'
    path_out = f'/app/uploads/{name_out}.mp3'

    with open(path_in, 'wb') as f:
        f.write(content)

    try:
        match preset:
            case Preset.BASSBOOST_TAZ:
                res = dj.bassboost_taz(path_in, path_out)
            case Preset.BASSBOOST_PACAN:
                res = dj.bassboost_pacan(path_in, path_out)
            case Preset.NIGHTCORE:
                res = dj.nightcore(path_in, path_out)
            case Preset.DAYCORE:
                res = dj.daycore(path_in, path_out)
            case Preset.REVERB:
                res = dj.reverb(path_in, path_out)
            case Preset.EARRAPE:
                res = dj.earrape(path_in, path_out)
            case Preset.CUSTOM:
                if cf is None:
                    return False, 'Missing process_cf list'
                res = dj.custom(path_in, path_out, cf)
            case _:
                return False, 'Unknown preset!'
    except Exception as e:
        print(f'Got exception back from dj module: {e}')
        return False, 'Processing error'
    finally:
        os.remove(path_in)

    return res, ''


async def make_remix(request: web.Request):
    if int(request.headers.get('Content-Length')) > get_app_settings().MAX_FILE_SIZE:
        return web.Response(status=400, text="Request body is too large")

    data = await request.post()
    if not ('file' in data and 'preset' in data and 'author' in data and type(data['file']) is FileField):
        return web.Response(status=400, text="Missing required fields")

    if not 1 < len(data['author']) < 25:
        return web.Response(status=400, text="Author field should range from 1 to 25 symbols")

    loop = asyncio.get_event_loop()
    name_in, name_out = str(uuid.uuid4()), str(uuid.uuid4())
    task = loop.run_in_executor(
        executor, process_upload,
        data['file'].file.read(),
        name_in,
        name_out,
        data['preset'],
        json.loads(data['process_cf']) if 'process_cf' in data else None
    )
    try:
        result, err = await asyncio.wait_for(task, 15)
    except asyncio.TimeoutError:
        return web.Response(status=504, text="File processing timed out")

    if not result:
        return web.Response(status=400, text=err)

    redis = RedisProvider.get_redis()
    await redis.set(f'remix_{name_out}', json.dumps(
        {'preset': data['preset'], 'author': data['author'], 'ts': int(time.time())}
    ))

    return web.Response(status=200, text=name_out)


async def get_remix(request: web.Request) -> web.Response:
    remix = request.query.get('name')
    if remix:
        redis = RedisProvider.get_redis()
        metadata = await redis.get(f'remix_{remix}')
        if metadata:
            return web.Response(status=200, text=metadata.decode())

    return web.Response(status=404, text="Remix not found")


async def serve_file(request: web.Request) -> web.Response | web.FileResponse:
    if not request.query.get('name'):
        return web.Response(status=404)
    path = os.path.join('/app/uploads', request.query.get('name'))
    if os.path.isfile(path):
        return web.FileResponse(path=path, headers=({'Content-Disposition': 'attachment'} if request.query.get('dl') else {}))
    else:
        return web.Response(status=404)


async def make_app() -> web.Application:
    app = web.Application(client_max_size=get_app_settings().MAX_FILE_SIZE)
    app.add_routes([
        web.get('/api/remix/metadata', get_remix),
        web.get('/api/file', serve_file),
        web.post('/api/remix/create', make_remix)
    ])
    loop = asyncio.get_event_loop()
    loop.create_task(hoover_job())
    return app


async def hoover_job() -> None:
    while True:
        redis = RedisProvider.get_redis()
        try:
            cutoff = time.time() - get_app_settings().HOOVER_FILE_TTL.total_seconds()
            for filename in os.listdir('/app/uploads'):
                file_path = os.path.join('/app/uploads', filename)

                if os.path.isdir(file_path):
                    continue

                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff:
                    os.remove(file_path)
                    await redis.delete(f'remix_{filename[:-4]}')
                    print(f"[HOOVER] Deleted: {file_path}")
            await asyncio.sleep(get_app_settings().HOOVER_SLEEP_TIME.total_seconds())
        except:
            pass


if __name__ == '__main__':
    executor = ThreadPoolExecutor(max_workers=64)
    RedisProvider.init_redis()
    web.run_app(make_app(), port=3400)
