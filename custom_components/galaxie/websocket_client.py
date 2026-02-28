"""WebSocket client for real-time Galaxie live race updates."""

import asyncio
import json
import logging
import random
from typing import Any, Callable

import aiohttp

_LOGGER = logging.getLogger(__name__)

INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0
BACKOFF_MULTIPLIER = 2.0


class GalaxieWebSocketClient:
    """Manages a WebSocket connection to the Galaxie backend for a single run."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        ws_url: str,
        run_id: str,
        on_run_detail: Callable[[dict[str, Any]], None],
        on_vehicle_list: Callable[[list], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self._session = session
        self._ws_url = ws_url
        self._run_id = run_id
        self._on_run_detail = on_run_detail
        self._on_vehicle_list = on_vehicle_list
        self._on_disconnect = on_disconnect
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._closing = False
        self._connected = False

    @property
    def connected(self) -> bool:
        """Return True if the WebSocket is currently connected."""
        return self._connected

    @property
    def run_id(self) -> str:
        """Return the run ID this client is connected to."""
        return self._run_id

    def start(self) -> None:
        """Start the WebSocket connection in a background task."""
        if self._task is None or self._task.done():
            self._closing = False
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._closing = True
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._connected = False

    async def _run(self) -> None:
        """Main loop: connect, receive messages, reconnect on failure."""
        backoff = INITIAL_BACKOFF
        while not self._closing:
            try:
                async with self._session.ws_connect(self._ws_url) as ws:
                    self._ws = ws
                    self._connected = True
                    backoff = INITIAL_BACKOFF
                    _LOGGER.info("WebSocket connected for run %s", self._run_id)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self._handle_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            _LOGGER.error(
                                "WebSocket error for run %s: %s",
                                self._run_id,
                                ws.exception(),
                            )
                            break
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.CLOSED,
                        ):
                            break

            except aiohttp.ClientError as err:
                _LOGGER.warning(
                    "WebSocket connection failed for run %s: %s",
                    self._run_id,
                    err,
                )
            except asyncio.CancelledError:
                return
            except Exception:
                _LOGGER.exception(
                    "Unexpected WebSocket error for run %s", self._run_id
                )
            finally:
                self._connected = False
                self._ws = None

            if self._closing:
                break

            jitter = random.uniform(0, backoff * 0.5)
            wait = min(backoff + jitter, MAX_BACKOFF)
            _LOGGER.debug(
                "WebSocket reconnecting for run %s in %.1fs",
                self._run_id,
                wait,
            )
            await asyncio.sleep(wait)
            backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)

        self._on_disconnect()

    def _handle_message(self, raw: str) -> None:
        """Route incoming WebSocket messages to appropriate handlers."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            _LOGGER.warning("Received non-JSON WebSocket message for run %s", self._run_id)
            return

        msg_type = data.get("type")
        if msg_type == "run_detail":
            payload = data.get("data")
            if payload is not None:
                self._on_run_detail(payload)
        elif msg_type == "vehicle_list":
            payload = data.get("data")
            if payload is not None:
                self._on_vehicle_list(payload)
        # All other message types (Arrow-encoded vehicle_laps, pit_stops, etc.)
        # are silently ignored.
