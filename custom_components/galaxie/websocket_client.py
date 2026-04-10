"""Centrifugo WebSocket client for real-time Galaxie live race updates.

The Galaxie backend publishes live run broadcasts (``run_detail``,
``vehicle_list``, and Arrow-encoded deltas) to a Centrifugo channel named
``run:{run_id}``. This module wraps the official ``centrifuge-python`` SDK
and exposes the same minimal callback surface the coordinator has always
relied on:

* ``on_run_detail(dict)``   — fired for each ``run_detail`` publication
* ``on_vehicle_list(list)`` — fired for each ``vehicle_list`` publication
* ``on_disconnect()``       — fired once after ``stop()`` (or a final failure)

All other publication types (``vehicle_laps``, ``pit_stops``,
``driver_results``, etc.) are silently ignored, matching prior behaviour.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

import aiohttp
from centrifuge import (
    Client,
    ClientEventHandler,
    ConnectedContext,
    DisconnectedContext,
    PublicationContext,
    SubscribedContext,
    SubscribingContext,
    SubscriptionErrorContext,
    SubscriptionEventHandler,
    UnauthorizedError,
    UnsubscribedContext,
)

from .const import BASE_URL, CENTRIFUGO_TOKEN_PATH, CENTRIFUGO_WS_PATH, WS_BASE_URL

_LOGGER = logging.getLogger(__name__)


class GalaxieWebSocketClient:
    """Manages a Centrifugo subscription for a single live run."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        run_id: str,
        on_run_detail: Callable[[dict[str, Any]], None],
        on_vehicle_list: Callable[[list], None],
        on_disconnect: Callable[[], None],
        *,
        ws_base_url: str = WS_BASE_URL,
        api_base_url: str = BASE_URL,
    ) -> None:
        self._session = session
        self._run_id = run_id
        self._on_run_detail = on_run_detail
        self._on_vehicle_list = on_vehicle_list
        self._on_disconnect = on_disconnect
        self._ws_url = f"{ws_base_url}{CENTRIFUGO_WS_PATH}"
        self._token_url = f"{api_base_url}{CENTRIFUGO_TOKEN_PATH}"
        self._channel = f"run:{run_id}"

        self._client: Client | None = None
        self._sub = None
        self._connected = False
        self._closing = False
        self._disconnect_fired = False

    @property
    def connected(self) -> bool:
        """Return True while the Centrifugo connection is up."""
        return self._connected

    @property
    def run_id(self) -> str:
        """Return the run ID this client is subscribed to."""
        return self._run_id

    async def _get_token(self) -> str:
        """Fetch a short-lived Centrifugo JWT from the Galaxie backend.

        The token endpoint is public (anonymous users are allowed) so no
        auth headers are required. Raises ``UnauthorizedError`` on 401/403
        so centrifuge-python treats it as a terminal auth failure.
        """
        try:
            async with self._session.post(self._token_url) as response:
                if response.status in (401, 403):
                    raise UnauthorizedError()
                if response.status != 200:
                    raise RuntimeError(
                        f"Centrifugo token endpoint returned {response.status}"
                    )
                data = await response.json()
                token = data.get("token", "")
                if not isinstance(token, str) or not token:
                    raise RuntimeError("Centrifugo token endpoint returned empty token")
                return token
        except UnauthorizedError:
            raise
        except Exception as err:  # noqa: BLE001 — surfaced via centrifuge-python
            _LOGGER.warning("Failed to fetch Centrifugo token: %s", err)
            raise

    def _handle_publication_data(self, data: Any) -> None:
        """Route a single publication envelope to the appropriate callback."""
        if not isinstance(data, dict):
            return
        msg_type = data.get("type")
        payload = data.get("data")
        if payload is None:
            return
        if msg_type == "run_detail" and isinstance(payload, dict):
            self._on_run_detail(payload)
        elif msg_type == "vehicle_list" and isinstance(payload, list):
            self._on_vehicle_list(payload)
        # All other types (Arrow-encoded vehicle_laps, pit_stops, etc.) ignored.

    def _build_client_events(self) -> ClientEventHandler:
        client_self = self

        class _ClientEvents(ClientEventHandler):
            async def on_connected(self, ctx: ConnectedContext) -> None:
                client_self._connected = True
                _LOGGER.info(
                    "Centrifugo connected for run %s", client_self._run_id
                )

            async def on_disconnected(self, ctx: DisconnectedContext) -> None:
                client_self._connected = False
                _LOGGER.info(
                    "Centrifugo disconnected for run %s: %s",
                    client_self._run_id,
                    getattr(ctx, "reason", ""),
                )

        return _ClientEvents()

    def _build_subscription_events(self) -> SubscriptionEventHandler:
        client_self = self

        class _SubEvents(SubscriptionEventHandler):
            async def on_subscribing(self, ctx: SubscribingContext) -> None:
                _LOGGER.debug(
                    "Centrifugo subscribing to %s", client_self._channel
                )

            async def on_subscribed(self, ctx: SubscribedContext) -> None:
                _LOGGER.info("Centrifugo subscribed to %s", client_self._channel)

            async def on_unsubscribed(self, ctx: UnsubscribedContext) -> None:
                _LOGGER.info(
                    "Centrifugo unsubscribed from %s: %s",
                    client_self._channel,
                    getattr(ctx, "reason", ""),
                )

            async def on_publication(self, ctx: PublicationContext) -> None:
                client_self._handle_publication_data(ctx.pub.data)

            async def on_error(self, ctx: SubscriptionErrorContext) -> None:
                _LOGGER.warning(
                    "Centrifugo subscription error on %s: %s",
                    client_self._channel,
                    ctx,
                )

        return _SubEvents()

    def start(self) -> None:
        """Open the Centrifugo connection and subscribe to the run channel."""
        if self._client is not None:
            return
        self._closing = False
        self._disconnect_fired = False

        self._client = Client(
            self._ws_url,
            events=self._build_client_events(),
            get_token=self._get_token,
            use_protobuf=False,
        )
        self._sub = self._client.new_subscription(
            self._channel,
            events=self._build_subscription_events(),
        )

        # centrifuge-python `connect()` / `subscribe()` are awaitables that
        # kick off background asyncio tasks. Schedule them without awaiting —
        # the coordinator calls `start()` from sync context.
        asyncio.create_task(self._sub.subscribe())
        asyncio.create_task(self._client.connect())

    async def stop(self) -> None:
        """Gracefully disconnect from Centrifugo."""
        self._closing = True
        client = self._client
        sub = self._sub
        self._client = None
        self._sub = None
        self._connected = False

        if sub is not None:
            try:
                await sub.unsubscribe()
            except Exception:  # noqa: BLE001 — best-effort teardown
                _LOGGER.debug(
                    "Error unsubscribing from %s", self._channel, exc_info=True
                )
        if client is not None:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001 — best-effort teardown
                _LOGGER.debug(
                    "Error disconnecting Centrifugo client for run %s",
                    self._run_id,
                    exc_info=True,
                )

        if not self._disconnect_fired:
            self._disconnect_fired = True
            self._on_disconnect()
