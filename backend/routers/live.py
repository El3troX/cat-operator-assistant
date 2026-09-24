import asyncio
import contextlib
from typing import Optional

from config import get_settings
from fastapi import APIRouter, WebSocket, status
from services import simulator
from services.events import EVENTS, TELEMETRY, bus

router = APIRouter(tags=["Live"])


async def _pump(websocket: WebSocket, queue: asyncio.Queue) -> None:
    while True:
        await websocket.send_json(await queue.get())


async def _stream(websocket: WebSocket, channel: str, initial: Optional[dict] = None) -> None:
    origin = websocket.headers.get("origin")
    # CORSMiddleware doesn't apply to WebSockets, so cross-site pages are refused here.
    if origin and not get_settings().origin_allowed(origin):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    with bus.subscribe(channel) as queue:
        if initial:
            queue.put_nowait(initial)
        pump = asyncio.create_task(_pump(websocket, queue))
        try:
            # Clients never send anything; receiving only tells us when they leave.
            while (await websocket.receive())["type"] != "websocket.disconnect":
                pass
        finally:
            pump.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await pump


@router.websocket("/ws/events")
async def events_stream(websocket: WebSocket):
    await _stream(websocket, EVENTS)


@router.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    latest = simulator.current.latest if simulator.current else None
    await _stream(websocket, TELEMETRY, initial=latest)
