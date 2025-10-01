from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping, MutableMapping
from datetime import UTC, datetime
from typing import Any

# -------- JSON Formatter --------


class JsonFormatter(logging.Formatter):
    def formatTime(
        self, record: logging.LogRecord, datefmt: str | None = None
    ) -> str:  # noqa: N802
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra_dict = getattr(record, "__extra__", {})
        if isinstance(extra_dict, dict):
            payload.update(extra_dict)

        if record.exc_info:
            exc_type = (
                record.exc_info[0].__name__ if record.exc_info and record.exc_info[0] else None
            )
            payload["exc_type"] = exc_type
            payload["exc_text"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


# -------- Loggers --------


def _install_access_logger(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("access")
    has_json = any(
        isinstance(h, logging.StreamHandler)
        and isinstance(getattr(h, "formatter", None), JsonFormatter)
        for h in logger.handlers
    )
    if not has_json:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


class ContextAdapter(logging.LoggerAdapter):
    """Permite passar extras por request (request_id, tenant_id, etc.)."""

    def process(self, msg: str, kwargs: MutableMapping[str, Any]):
        extra_obj = kwargs.pop("extra", None)

        base: dict[str, Any]
        if isinstance(self.extra, Mapping):
            base = dict(self.extra)
        else:
            base = {}

        extra_add: dict[str, Any]
        if isinstance(extra_obj, Mapping):
            extra_add = dict(extra_obj)
        else:
            extra_add = {}

        merged = base.copy()
        merged.update(extra_add)

        kwargs["extra"] = {"__extra__": merged}
        return msg, kwargs


def get_logger(name: str, base_extra: Mapping[str, Any] | None = None) -> logging.Logger:
    logger = _install_access_logger() if name == "access" else logging.getLogger(name)
    # LoggerAdapter retorna LoggerAdapter; expor como Logger é suficiente para uso
    # e evita ruído no typing.
    return ContextAdapter(logger, dict(base_extra or {}))  # type: ignore[return-value]
