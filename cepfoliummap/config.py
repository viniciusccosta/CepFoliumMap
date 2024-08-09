import logging
from datetime import datetime
from pathlib import Path

from decouple import config
from rich.logging import RichHandler


def config_logging():
    # Handlers:
    file_handler = logging.FileHandler(
        encoding="utf-8",
        filename=f"logs/{datetime.now():%Y-%m-%d-%H-%M-%S}.log",
        mode="w",
    )
    stream_handler = RichHandler(
        rich_tracebacks=True,
    )

    # Logging:
    logging.basicConfig(
        level=config("LOGGING_LEVEL", logging.INFO),
        encoding="utf-8",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            file_handler,
            stream_handler,
        ],
    )

    # Outros loggers:
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.INFO)

    logging.debug("Logging configurado")


def create_directories():
    logging.debug("Criando diretórios")

    Path("mapas/").mkdir(parents=True, exist_ok=True)
    Path("brasilapi/").mkdir(parents=True, exist_ok=True)
    Path("logs/").mkdir(parents=True, exist_ok=True)
    Path("geodecode/").mkdir(parents=True, exist_ok=True)
    Path("merges/").mkdir(parents=True, exist_ok=True)

    logging.debug("Diretórios criados")


def initial_config():
    config_logging()
    create_directories()
