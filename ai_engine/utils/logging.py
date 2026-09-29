"""
Shared logging utility for the AI engine.

Identical redaction rules to the backend logger — passwords, tokens,
and RTSP URLs with embedded credentials are never emitted.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, MutableMapping
import re

# pyright: ignore [reportMissingImports]
import structlog

_REDACT_KEYS: frozenset[str] = frozenset(
    {"password", "token", "api_key", "rtsp_url", "secret", "authorization"}
)
_RTSP_RE = re.compile(r"rtsp://[^\s@]*:[^\s@]*@", re.IGNORECASE)


def _redact_processor(
    logger: Any,
    method: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    for key in list(event_dict.keys()):
        if key.lower() in _REDACT_KEYS:
            event_dict[key] = "[REDACTED]"
        elif isinstance(event_dict[key], str):
            event_dict[key] = _RTSP_RE.sub("rtsp://[REDACTED]@", event_dict[key])
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    level = logging.getLevelName(log_level.upper())
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
