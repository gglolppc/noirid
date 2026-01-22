import logging
import sys
from enum import Enum
from typing import Union


class Env(str, Enum):
    DEV = "dev"
    PROD = "prod"


def _normalize_env(env: Union[Env, str]) -> Env:
    if isinstance(env, Env):
        return env
    try:
        return Env(env)
    except ValueError:
        return Env.PROD


def setup_logging(env: Union[Env, str]) -> None:
    normalized_env = _normalize_env(env)
    log_level = logging.DEBUG if normalized_env == Env.DEV else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Явно говорим выводить в поток
        ],
        force=True,
    )

    # Можно сразу приглушить слишком болтливые библиотеки
    access_level = logging.INFO if normalized_env == Env.DEV else logging.WARNING
    logging.getLogger("uvicorn.access").setLevel(access_level)
