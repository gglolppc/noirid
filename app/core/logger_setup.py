import logging
import sys
from enum import Enum


class Env(str, Enum):
    DEV = "dev"
    PROD = "prod"


def setup_logging(env: Env) -> None:
    # Используем dictConfig для полного контроля
    log_level = logging.DEBUG if env == Env.DEV else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Явно говорим выводить в поток
        ]
    )

    # Можно сразу приглушить слишком болтливые библиотеки
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)