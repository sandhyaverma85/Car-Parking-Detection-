"""
Structured, safe application logging.

Uses structlog so that every log entry is a structured JSON object,
making it easy to ingest into log-aggregation tools.

Security rules enforced here:
  - Passwords, tokens, and API keys are NEVER logged.
  - RTSP URLs (which may contain credentials) are redacted.
  - Stack traces are only emitted at DEBUG level; production uses INFO+.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path
from typing import Any, MutableMapping

import structlog


# ── Sensitive-value redaction ─────────────────────────────────────────────────

_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "password_hash",
        "jwt_secret",
        "secret",
        "token",
        "access_token",
        "api_key",
        "rtsp_url",
        "rtsp",
        "authorization",
        "cookie",
        "x-api-key",
    }
)

_RTSP_RE = re.compile(r"rtsp://[^\s@]*:[^\s@]*@", re.IGNORECASE)


def _redact_processor(
    logger: Any,  # noqa: ANN401 – structlog typing
    method: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Replace sensitive keys with '[REDACTED]' before the record is emitted."""
    for key in list(event_dict.keys()):
        if key.lower() in _REDACT_KEYS:
            event_dict[key] = "[REDACTED]"
        elif isinstance(event_dict[key], str):
            # Redact RTSP credentials embedded in strings.
            event_dict[key] = _RTSP_RE.sub("rtsp://[REDACTED]@", event_dict[key])
    return event_dict


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configure structlog + stdlib logging.

    Call once at application startup.  Safe to call multiple times
    (idempotent — subsequent calls are no-ops).
    """
    level = logging.getLevelName(log_level.upper())

    # Ensure log directory exists.
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
        )

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=handlers,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structlog logger."""
    return structlog.get_logger(name)
