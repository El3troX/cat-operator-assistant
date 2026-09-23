import asyncio
from contextlib import contextmanager
from typing import Iterator, Optional

from pydantic import BaseModel

EVENTS = "events"
TELEMETRY = "telemetry"


class EventBus:
    """In-process fan-out from publishers to WebSocket subscribers.

    Sync route handlers run in a threadpool, so publish() hands messages to the event loop
    thread-safely. A slow subscriber loses its oldest messages rather than blocking others.
    """

    def __init__(self, queue_size: int = 200) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue_size = queue_size

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @contextmanager
    def subscribe(self, channel: str) -> Iterator[asyncio.Queue]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.setdefault(channel, set()).add(queue)
        try:
            yield queue
        finally:
            self._subscribers[channel].discard(queue)

    def publish(self, channel: str, message: dict) -> None:
        # No loop bound (e.g. in-process tests without lifespan): nobody can be listening.
        if self._loop is None or self._loop.is_closed():
            return
        self._loop.call_soon_threadsafe(self._fan_out, channel, message)

    def _fan_out(self, channel: str, message: dict) -> None:
        for queue in list(self._subscribers.get(channel, ())):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(message)


bus = EventBus()


def publish_event(event_type: str, payload: BaseModel) -> None:
    bus.publish(EVENTS, {"type": event_type, "data": payload.model_dump(mode="json")})
