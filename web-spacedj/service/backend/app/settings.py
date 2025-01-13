import datetime
from functools import lru_cache
from datetime import datetime, timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    MAX_FILE_SIZE: int = 1048576 * 3
    HOOVER_SLEEP_TIME: timedelta = timedelta(minutes=4)
    HOOVER_FILE_TTL: timedelta = timedelta(minutes=15)

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
