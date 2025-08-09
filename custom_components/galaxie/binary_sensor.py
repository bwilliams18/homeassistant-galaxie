"""Binary sensor platform for Galaxie integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN, DEVICE_CLASS_LIVE_STATUS
from .device import get_live_status_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Galaxie binary sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    _LOGGER.info("Setting up Galaxie binary sensors")

    entities = [LiveRaceStatusBinarySensor(coordinator)]

    _LOGGER.info("Created %d binary sensors", len(entities))
    async_add_entities(entities)


class LiveRaceStatusBinarySensor(BinarySensorEntity):
    """Live race status binary sensor."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = "live_race_status"
        self._attr_name = "Live Race Status"
        self._attr_device_class = DEVICE_CLASS_LIVE_STATUS
        self._attr_icon = "mdi:flag-checkered"
        self._attr_device_info = get_live_status_device()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "live_race" in self.coordinator.data
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if there is a live race."""
        data = self.coordinator.data
        if not data or "live_race" not in data:
            _LOGGER.debug(
                "No live_race data available for binary sensor %s", self._attr_name
            )
            return False

        live_races = data["live_race"]
        # Check if there are any live races
        is_live = (
            isinstance(live_races, list) 
            and len(live_races) > 0 
            and all(isinstance(race, dict) for race in live_races)
        )
        _LOGGER.debug(
            "Binary sensor %s: live_races=%s, is_live=%s",
            self._attr_name,
            live_races,
            is_live,
        )
        return is_live
