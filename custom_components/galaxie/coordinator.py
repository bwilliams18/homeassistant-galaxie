"""Data coordinator for Galaxie integration."""

from __future__ import annotations

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
    BASE_URL,
    WS_BASE_URL,
    API_ENDPOINTS,
    UPDATE_INTERVAL_PREVIOUS_NEXT,
    UPDATE_INTERVAL_LIVE,
    UPDATE_INTERVAL_CONFIG,
)
from .websocket_client import GalaxieWebSocketClient

_LOGGER = logging.getLogger(__name__)


class GalaxieDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Galaxie data."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL_LIVE,
        )
        self.session = session
        self.data = {}
        self._config_data: dict | None = None
        self._last_config_fetch: datetime | None = None
        self._ws_client: GalaxieWebSocketClient | None = None
        self._current_run_id: str | None = None
        self._ws_live_data: dict | None = None

    @property
    def backend_version(self) -> str:
        """Return the backend version string."""
        if self._config_data:
            return self._config_data.get("version", "unknown")
        return "unknown"

    def _should_fetch_config(self) -> bool:
        """Return True if config data should be refreshed."""
        if self._config_data is None or self._last_config_fetch is None:
            return True
        return (datetime.now() - self._last_config_fetch) >= UPDATE_INTERVAL_CONFIG

    def _ws_on_run_detail(self, data: dict) -> None:
        """Handle run_detail push from WebSocket."""
        self._ws_live_data = data
        if self.data is not None:
            self.data["live_race"] = [data]
            self.async_set_updated_data(self.data)

    def _ws_on_disconnect(self) -> None:
        """Handle WebSocket disconnect -- resume REST polling for live data."""
        _LOGGER.info("WebSocket disconnected, resuming REST polling for live data")
        self._ws_client = None
        self._current_run_id = None
        self._ws_live_data = None

    async def _manage_ws_connection(self, live_race_data: list) -> None:
        """Start/stop WebSocket based on live race availability."""
        if live_race_data and isinstance(live_race_data[0], dict):
            run_id = live_race_data[0].get("id")
            if run_id and run_id != self._current_run_id:
                # New or different run -- disconnect old, connect new
                if self._ws_client:
                    await self._ws_client.stop()

                self._current_run_id = run_id
                ws_url = f"{WS_BASE_URL}/ws/runs/{run_id}/"
                self._ws_client = GalaxieWebSocketClient(
                    session=self.session,
                    ws_url=ws_url,
                    run_id=run_id,
                    on_run_detail=self._ws_on_run_detail,
                    on_disconnect=self._ws_on_disconnect,
                )
                self._ws_client.start()
                _LOGGER.info("Started WebSocket for run %s", run_id)
        else:
            # No live race -- disconnect WS if active
            if self._ws_client:
                _LOGGER.info("No live race, stopping WebSocket")
                await self._ws_client.stop()
                self._ws_client = None
                self._current_run_id = None
                self._ws_live_data = None

    async def async_shutdown(self) -> None:
        """Clean up WebSocket connection on unload."""
        if self._ws_client:
            await self._ws_client.stop()
            self._ws_client = None
            self._current_run_id = None
            self._ws_live_data = None

    async def _async_update_data(self):
        """Update data via API."""
        _LOGGER.debug("Starting Galaxie data update")
        try:
            fetch_config = self._should_fetch_config()

            # If WS is connected and delivering data, skip REST live fetch
            ws_active = self._ws_client is not None and self._ws_client.connected

            tasks = [
                self._fetch_previous_race(),
                self._fetch_next_race(),
            ]
            if not ws_active:
                tasks.append(self._fetch_live_race())
            if fetch_config:
                tasks.append(self._fetch_config())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            previous_race = results[0]
            next_race = results[1]

            idx = 2
            if not ws_active:
                live_race = results[idx]
                idx += 1
            else:
                # Use WS data
                live_race = [self._ws_live_data] if self._ws_live_data else []

            if fetch_config and idx < len(results):
                config_result = results[idx]
                if isinstance(config_result, dict):
                    self._config_data = config_result
                    self._last_config_fetch = datetime.now()

            result = {
                "previous_race": (
                    previous_race if isinstance(previous_race, list) else []
                ),
                "next_race": (
                    next_race if isinstance(next_race, list) else []
                ),
                "live_race": (
                    live_race if isinstance(live_race, list) else []
                ),
                "config": self._config_data,
            }

            # Manage WebSocket lifecycle based on live race presence
            await self._manage_ws_connection(result["live_race"])

            _LOGGER.debug(
                "Galaxie data update: previous=%d, next=%d, live=%d, ws=%s",
                len(result["previous_race"]),
                len(result["next_race"]),
                len(result["live_race"]),
                "connected" if ws_active else "off",
            )

            return result

        except Exception as err:
            _LOGGER.error("Error in Galaxie data update: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _fetch_previous_race(self):
        """Fetch previous race data."""
        url = f"{BASE_URL}{API_ENDPOINTS['previous_race']}"
        _LOGGER.debug("Fetching previous race data from: %s", url)
        try:
            async with self.session.get(url) as response:
                _LOGGER.debug("Previous race response status: %s", response.status)
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(
                        "Previous race data received: %d items",
                        len(data) if isinstance(data, list) else 0,
                    )
                    return data
                else:
                    _LOGGER.warning(
                        "Previous race API returned status %s", response.status
                    )
                    return []
        except Exception as e:
            _LOGGER.error("Error fetching previous race data: %s", e)
            return []

    async def _fetch_next_race(self):
        """Fetch next race data."""
        url = f"{BASE_URL}{API_ENDPOINTS['next_race']}"
        _LOGGER.debug("Fetching next race data from: %s", url)
        try:
            async with self.session.get(url) as response:
                _LOGGER.debug("Next race response status: %s", response.status)
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(
                        "Next race data received: %d items",
                        len(data) if isinstance(data, list) else 0,
                    )
                    return data
                else:
                    _LOGGER.warning("Next race API returned status %s", response.status)
                    return []
        except Exception as e:
            _LOGGER.error("Error fetching next race data: %s", e)
            return []

    async def _fetch_live_race(self):
        """Fetch live race data."""
        url = f"{BASE_URL}{API_ENDPOINTS['live']}"
        _LOGGER.debug("Fetching live race data from: %s", url)
        try:
            async with self.session.get(url) as response:
                _LOGGER.debug("Live race response status: %s", response.status)
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(
                        "Live race data received: %d items",
                        len(data) if isinstance(data, list) else 0,
                    )
                    return data
                else:
                    _LOGGER.warning("Live race API returned status %s", response.status)
                    return []
        except Exception as e:
            _LOGGER.error("Error fetching live race data: %s", e)
            return []

    async def _fetch_config(self):
        """Fetch backend config data."""
        url = f"{BASE_URL}{API_ENDPOINTS['config']}"
        _LOGGER.debug("Fetching config data from: %s", url)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug(
                        "Config data received: version=%s, environment=%s",
                        data.get("version"),
                        data.get("environment"),
                    )
                    return data
                else:
                    _LOGGER.warning("Config API returned status %s", response.status)
                    return None
        except Exception as e:
            _LOGGER.error("Error fetching config data: %s", e)
            return None
