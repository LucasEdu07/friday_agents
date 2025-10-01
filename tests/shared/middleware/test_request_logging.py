# tests/shared/middleware/test_request_logging.py
from __future__ import annotations

import io
import logging

from fastapi import FastAPI
from starlette.testclient import TestClient

from services.shared.logging_utils import JsonFormatter
from services.shared.middleware.request_logging import RequestLoggingMiddleware
from services.shared.middleware_utils import RequestIdMiddleware


def make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/v1/ok")
    def ok():
        return {"ok": True}

    @app.get("/v1/fail")
    def fail():
        raise RuntimeError("boom")

    # Lembrete: o último adicionado roda primeiro.
    app.add_middleware(RequestLoggingMiddleware)  # roda depois do RequestId
    app.add_middleware(RequestIdMiddleware)  # garante request_id antes

    return app


def _attach_buffer_logger() -> tuple[logging.Logger, io.StringIO, logging.Handler]:
    """
    Anexa um handler JSON próprio ao logger 'access' e retorna (logger, buffer, handler)
    para leitura e remoção depois.
    """
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("access")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger, buf, handler


def _detach_buffer_logger(logger: logging.Logger, handler: logging.Handler) -> None:
    try:
        logger.removeHandler(handler)
    finally:
        handler.close()


def test_logs_have_request_id():
    app = make_app()
    client = TestClient(app)

    logger, buf, handler = _attach_buffer_logger()
    try:
        r = client.get("/v1/ok")
        assert r.status_code == 200

        handler.flush()
        out = buf.getvalue()

        assert "request.end" in out
        assert '"request_id":' in out
        assert '"path": "/v1/ok"' in out
        assert '"status": 200' in out
    finally:
        _detach_buffer_logger(logger, handler)


def test_logs_on_error_have_stacktrace():
    app = make_app()
    client = TestClient(app, raise_server_exceptions=False)

    logger, buf, handler = _attach_buffer_logger()
    try:
        r = client.get("/v1/fail")
        assert r.status_code == 500

        handler.flush()
        out = buf.getvalue()

        # Em alguns stacks, ExceptionsMiddleware captura e devolve 500 sem
        # estourar até o nosso middleware; nesse caso, vem 'request.end' com 500.
        # Em outros, a exceção sobe e logamos 'request.error'.
        assert '"status": 500' in out
        assert ('"message": "request.error"' in out) or ('"message": "request.end"' in out)
        if '"message": "request.error"' in out:
            assert '"exc_text":' in out
    finally:
        _detach_buffer_logger(logger, handler)
