import json
import logging
import re
import time
import uuid
from contextvars import ContextVar

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger("api")

_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_QUIET_PATHS = {"/health"}


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class _JsonFormatter(logging.Formatter):
    _EXTRA_FIELDS = ("method", "path", "status", "duration_ms")

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        for field in self._EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str, json_logs: bool) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(
        _JsonFormatter()
        if json_logs
        else logging.Formatter("%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # RequestContextMiddleware logs every request with its id and timing, so uvicorn's access log would duplicate it.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestContextMiddleware:
    """Tags each request with an id, logs it, and turns unhandled errors into JSON 500s.

    Must sit inside CORSMiddleware so error responses still carry CORS headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex[:12]
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message).append("X-Request-ID", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception("Unhandled error on %s %s", scope["method"], scope["path"])
            if response_started:
                raise
            status_code = 500
            response = JSONResponse(
                {"detail": "Internal server error", "request_id": request_id},
                status_code=500,
                headers={"X-Request-ID": request_id},
            )
            await response(scope, receive, send)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            level = logging.DEBUG if scope["path"] in _QUIET_PATHS and status_code < 400 else logging.INFO
            logger.log(
                level,
                "%s %s -> %s (%.1f ms)",
                scope["method"],
                scope["path"],
                status_code,
                duration_ms,
                extra={"method": scope["method"], "path": scope["path"], "status": status_code, "duration_ms": duration_ms},
            )
            request_id_var.reset(token)
