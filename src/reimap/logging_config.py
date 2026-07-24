"""Logging configuration for reimap.

Sets up a console handler and a rotating file handler under the platform log
directory. All modules obtain loggers via :func:`get_logger`.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .app_dirs import log_dir

_CONFIGURED = False
_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging handlers exactly once.

    Args:
        level: The minimum level emitted by the console handler.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger("reimap")
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            log_dir() / "reimap.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # If the log directory is not writable we still keep console logging.
        root.warning("Could not open log file; continuing with console logging only.")

    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child logger.

    Args:
        name: A dotted suffix appended to the ``reimap`` root logger.
    """
    return logging.getLogger(f"reimap.{name}")
