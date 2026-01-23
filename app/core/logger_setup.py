import logging
import sys
from enum import Enum
from typing import Union


class Env(str, Enum):
    DEV = "dev"
    PROD = "prod"


def setup_logging(env: Union[Env, str]) -> None:
    log_level = logging.DEBUG if env == Env.DEV else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(
        "app.log",
        encoding="utf-8",
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    # Приручаем uvicorn
    for name in ("uvicorn", "uvicorn.error", "fastapi"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
        logging.getLogger(name).setLevel(log_level)

    # access-логи — только WARN в PROD
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.access").setLevel(
        logging.INFO if env == Env.DEV else logging.WARNING
    )

    logging.info("Logging initialized (%s)", env)
