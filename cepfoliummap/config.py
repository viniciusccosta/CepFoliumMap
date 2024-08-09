import logging
from datetime import datetime
from pathlib import Path

from decouple import config
from rich.logging import RichHandler


def config_logging():
    # Configurando logging:
    file_handler = logging.FileHandler(
        filename=f"logs/{datetime.now():%Y-%m-%d-%H-%M-%S}.log",
        mode="w",
        encoding="utf-8",
    )
    stream_handler = RichHandler(rich_tracebacks=True)

    logging.basicConfig(
        level=config("LOGGING_LEVEL", logging.INFO),
        encoding="utf-8",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            stream_handler,
        ],
    )


def create_directories():
    Path("mapas/").mkdir(parents=True, exist_ok=True)
    Path("brasilapi/").mkdir(parents=True, exist_ok=True)
    Path("logs/").mkdir(parents=True, exist_ok=True)
    Path("geodecode/").mkdir(parents=True, exist_ok=True)
    Path("merges/").mkdir(parents=True, exist_ok=True)


def initial_config():
    create_directories()
