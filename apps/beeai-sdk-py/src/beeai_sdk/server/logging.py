# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import logging
import logging.config
import sys
from logging import getLevelName
from typing import ClassVar

logger = logging.getLogger("beeai_sdk")


class ColoredFormatter(logging.Formatter):
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        return f"{color}{log_message}{reset}"


# Dictionary configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,
            "format": "%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(asctime)s | %(levelname)-8s | %(message)s", "datefmt": "%H:%M:%S"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "colored", "stream": sys.stdout}},
    "loggers": {
        "root": {"level": "INFO", "handlers": ["console"]},
        "httpx": {"level": "WARNING"},
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}


def configure_logger(level: int | str | None = None) -> None:
    if level is not None:
        level = level if isinstance(level, int) else logging.getLevelNamesMapping()[level.upper()]
        logging.config.dictConfig(
            {
                **LOGGING_CONFIG,
                "loggers": {"root": {"level": getLevelName(level), "handlers": ["console"]}},
            }
        )
    else:
        logging.config.dictConfig(LOGGING_CONFIG)
