"""
BizPilot AI - Centralized Logger
Loguru-based logger with console + rotating file handlers,
optional structured JSON output, and sensitive-data masking.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Union

from loguru import logger as _base_logger

# ---------------------------------------------------------------------------
# Sensitive-data patterns to mask in log messages
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # API keys: long alphanumeric strings after common key names
    (re.compile(r"(api[_-]?key\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(groq[_-]?api[_-]?key\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(serpapi[_-]?key\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    # Passwords
    (re.compile(r"(password\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(smtp[_-]?password\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    # Secret key
    (re.compile(r"(secret[_-]?key\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    # JWT / Bearer tokens
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1***REDACTED***"),
    # Generic tokens
    (re.compile(r"(token\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    # Database connection strings with credentials
    (re.compile(r"(://[^:]+:)[^@]+(@)", re.IGNORECASE), r"\1***REDACTED***\2"),
]


def _mask_sensitive(message: str) -> str:
    """Apply all sensitive-data patterns to a log message string."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class _SensitiveFilter:
    """Loguru sink-level filter that masks sensitive data before writing."""

    def __call__(self, record: dict) -> bool:  # noqa: ANN001
        record["message"] = _mask_sensitive(record["message"])
        if record.get("extra"):
            safe_extra: dict = {}
            for k, v in record["extra"].items():
                safe_extra[k] = _mask_sensitive(str(v)) if isinstance(v, str) else v
            record["extra"] = safe_extra
        return True


# ---------------------------------------------------------------------------
# Logger configuration
# ---------------------------------------------------------------------------

_LOGS_DIR = Path("logs")
_LOGS_DIR.mkdir(exist_ok=True)

_LOG_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

_LOG_FORMAT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} | {message}"
)

_LOG_FORMAT_JSON = (
    '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
    '"level": "{level}", '
    '"name": "{name}", '
    '"function": "{function}", '
    '"line": {line}, '
    '"message": "{message}"}}'
)

_sensitive_filter = _SensitiveFilter()


def _configure_logger(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Remove defaults and add console + file handlers."""
    _base_logger.remove()  # Remove the default stderr handler

    # Console handler
    _base_logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=_LOG_FORMAT_JSON if json_logs else _LOG_FORMAT_CONSOLE,
        colorize=not json_logs,
        filter=_sensitive_filter,
        backtrace=True,
        diagnose=True,
    )

    # Rotating file handler – general log
    _base_logger.add(
        _LOGS_DIR / "bizpilot.log",
        level=log_level.upper(),
        format=_LOG_FORMAT_JSON if json_logs else _LOG_FORMAT_FILE,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        enqueue=True,         # thread-safe async writes
        filter=_sensitive_filter,
        backtrace=True,
        diagnose=False,       # avoid leaking locals to disk
    )

    # Rotating file handler – errors only
    _base_logger.add(
        _LOGS_DIR / "bizpilot_errors.log",
        level="ERROR",
        format=_LOG_FORMAT_JSON if json_logs else _LOG_FORMAT_FILE,
        rotation="5 MB",
        retention="60 days",
        compression="gz",
        enqueue=True,
        filter=_sensitive_filter,
        backtrace=True,
        diagnose=False,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """
    Initialise the global Loguru logger.

    Call once at application startup (e.g. in ``main.py``)::

        from app.utils.logger import setup_logging
        setup_logging(log_level="INFO", json_logs=False)
    """
    _configure_logger(log_level=log_level, json_logs=json_logs)
    _base_logger.info("Logging initialised | level={} | json={}", log_level, json_logs)


def get_logger(name: str):  # noqa: ANN201
    """
    Return a child logger bound with a *name* context variable.

    Usage::

        from app.utils.logger import get_logger
        log = get_logger(__name__)
        log.info("Hello from {}", __name__)
    """
    return _base_logger.bind(name=name)


# Provide a module-level convenience logger for quick imports
log = get_logger("bizpilot")

# Apply default configuration immediately so the logger works even if
# setup_logging() is never called explicitly.
_configure_logger()
