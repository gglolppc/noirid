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

    # 1. Формат логов
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # 2. Настройка корневого (root) логгера
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    # 3. Список логгеров, которые нужно "приручить"
    # Uvicorn по умолчанию имеет свои настройки, которые затирают basicConfig
    intercept_loggers = (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    )

    for logger_name in intercept_loggers:
        logger = logging.getLogger(logger_name)
        # Удаляем все старые обработчики, которые мог воткнуть uvicorn
        logger.handlers = []
        # Настраиваем уровень
        if logger_name == "uvicorn.access":
            # В PROD скрываем лишний шум посещений, в DEV — оставляем INFO
            logger.setLevel(logging.INFO if normalized_env == Env.DEV else logging.WARNING)
        else:
            logger.setLevel(log_level)

        # Указываем, что логи должны уходить в родительский (root) логгер
        logger.propagate = True

    logging.info(f"Logging initialized in {normalized_env} mode with level {logging.getLevelName(log_level)}")
    logging.getLogger("python_multipart").setLevel(logging.INFO)
    logging.getLogger("python_multipart.multipart").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
