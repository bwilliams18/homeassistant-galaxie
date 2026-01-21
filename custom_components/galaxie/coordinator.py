"""Data coordinator for Galaxie integration."""

import asyncio
import logging
import aiohttp
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
    BASE_URL,
    API_ENDPOINTS,
    UPDATE_INTERVAL_PREVIOUS_NEXT,
    UPDATE_INTERVAL_LIVE,
)

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

    async def _async_update_data(self):
        """Update data via API."""
        _LOGGER.info("Starting Galaxie data update")
        try:
            # Fetch all data concurrently
            previous_race, next_race, live_race = await asyncio.gather(
                self._fetch_previous_race(),
                self._fetch_next_race(),
                self._fetch_live_race(),
                return_exceptions=True,
            )

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
            }

            _LOGGER.info("Galaxie data update completed successfully")
            _LOGGER.info(
                "Data summary: previous_race=%d items, next_race=%d items, live_race=%d items",
                len(result["previous_race"]),
                len(result["next_race"]),
                len(result["live_race"]),
            )

            # Debug: Log the actual data structure
            if result["previous_race"]:
                _LOGGER.debug(
                    "Previous race data sample: %s", result["previous_race"][0]
                )
            if result["next_race"]:
                _LOGGER.debug("Next race data sample: %s", result["next_race"][0])
            if result["live_race"]:
                _LOGGER.debug("Live race data sample: %s", result["live_race"][0])

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
